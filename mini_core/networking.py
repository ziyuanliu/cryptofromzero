import binascii
import logging
import mini_core.mempool as mempool
import os
import random
import socket
import socketserver
import threading
import time

import mini_core.block as block

from mini_core.chain import get_active_chain, chain_lock, connect_block, locate_block

from typing import Iterable, NamedTuple, Callable

from mini_core.transaction import Transaction

from mini_core.utxo_set import utxo_set

from mini_core.utils import deserialize, serialize

logger = logging.getLogger(__name__)

peer_hostnames = {p for p in os.environ.get('TC_PEERS', '').split(',') if p}

ibd_done = threading.Event()

PORT = os.environ.get('TC_PORT', 8888)


def get_ibd_done():
    return ibd_done


def get_peer_hostnames():
    return peer_hostnames


def int_to_8bytes(a: int) -> bytes:
    return binascii.unhexlify(f'{a:0{8}x}')


def encode_socket_data(data: object) -> bytes:
    """
    Our protocol is: first 4 bytes signify msg length
    """

    to_send = serialize(data).encode()
    return int_to_8bytes(len(to_send)) + to_send


class GetBlocksMsg(NamedTuple):
    """
    See https://bitcoin.org/en/developer-guide#blocks-first
    initial block sync
    """

    from_blockid: str

    CHUNK_SIZE = 50

    def handle(self, sock, peer_hostname):
        logger.debug(f'[p2p] recv getblocks from {peer_hostname}')

        _, height, _ = locate_block(self.from_blockid, get_active_chain())

        height = height or 1

        with chain_lock:
            blocks = get_active_chain()[height:(height + self.CHUNK_SIZE)]

        logger.debug(f'[p2p] sending {len(blocks)} to {peer_hostname}')
        send_to_peer(InvMsg(blocks), peer_hostname)


class InvMsg(NamedTuple):
    blocks: Iterable[str]

    def handle(self, sock, peer_hostname):
        logger.info(f'[p2p] recv inv from {peer_hostname}')

        new_blocks = [b for b in self.blocks if not locate_block(b.id)[0]]

        if not new_blocks:
            logger.info('[p2p] initial block download complete')
            ibd_done.set()
            return

        for block in new_blocks:
            connect_block(block)

        new_tip_id = get_active_chain()[-1].id
        logger.info(f'[p2p] continuing initial block download at {new_tip_id}')

        with chain_lock:
            # Recursive call to continue the initial block sync
            send_to_peer(GetBlocksMsg(new_tip_id))


class GetUTXOsMsg(NamedTuple):

    def handle(self, sock, peer_hostname):
        sock.sendall(encode_socket_data(list(utxo_set.items())))


class GetMempoolMsg(NamedTuple):
    """
    List the mempool
    """

    def handle(self, sock, peer_hostname):
        sock.sendall(encode_socket_data(list(mempool.mempool.keys())))


class GetActiveChainMsg(NamedTuple):
    """
    Get the active chain in its entirety
    """

    def handle(self, sock, peer_hostname):
        sock.sendall(encode_socket_data(list(get_active_chain())))


class AddPeerMsg(NamedTuple):
    peer_hostname: str

    def handle(self, sock, peer_hostname):
        peer_hostnames.add(self.peer_hostname)


def read_all_from_socket(req) -> object:
    """
    First 4 bytes signify message length
    """

    data = b''

    msg_len = int(binascii.hexlify(req.recv(4) or b'\x00'), 16)

    while msg_len > 0:
        tdat = req.recv(1024)
        data += tdat
        msg_len -= len(tdat)

    return deserialize(data.decode()) if data else None


def send_to_peer(data, peer=None):
    """
    Send a message to a (by default) random peer.
    """
    global peer_hostnames

    peer = peer or random.choice(list(peer_hostnames))
    tries_left = 3

    while tries_left > 0:
        try:
            with socket.create_connection((peer, PORT), timeout=1) as s:
                s.sendall(encode_socket_data(data))
                logger.info(f'sending this {data} to {peer} {PORT}')
        except Exception:
            logger.exception(f'failed to send to peer {peer}')
            tries_left -= 1
            time.sleep(2)
        else:
            return

    logger.info(f'[p2p] removing dead peer {peer}')
    peer_hostnames = {x for x in peer_hostnames if x != peer}


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class TCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = read_all_from_socket(self.request)
        peer_hostname = self.request.getpeername()[0]
        peer_hostnames.add(peer_hostname)

        if hasattr(data, 'handle') and isinstance(data.handle, Callable):
            data.handle(self.request, peer_hostname)
        elif isinstance(data, Transaction):
            logger.info(f'received txn {data.id} for peer {peer_hostname}')
            mempool.add_txn_to_mempool(data)
        elif isinstance(data, block.Block):
            logger.info(f'received block {data.id} from peer {peer_hostname}')
            connect_block(data)

import logging
import os
import threading
import ecdsa

from mini_core.block import Block
from mini_core.chain import load_from_disk, get_active_chain
from mini_core.transaction import OutPoint, Transaction, TxIn, TxOut, UnspentTxOut, SignatureScript
from mini_core.networking import GetActiveChainMsg, GetMempoolMsg, GetUTXOsMsg, GetBlocksMsg, InvMsg, TCPHandler, ThreadedTCPServer, send_to_peer, get_ibd_done, get_peer_hostnames
from mini_core.proof_of_work import mine_forever
from mini_core.validation import build_spend_message


logging.basicConfig(
    level=getattr(logging, os.environ.get('TC_LOG_LEVEL', 'INFO')),
    format='[%(asctime)s][%(module)s:%(lineno)d] %(levelname)s %(message)s')

logger = logging.getLogger(__name__)

PORT = os.environ.get('TC_PEER', 8888)


def make_txin(signing_key, outpoint: OutPoint, txout: TxOut) -> TxIn:
    sequence = 0
    pk = signing_key.verifying_key.to_string()
    spend_msg = build_spend_message(outpoint, pk, sequence, [txout])

    return TxIn(signature=SignatureScript(unlock_sig=signing_key.sign(spend_msg), unlock_pk=pk), outpoint=outpoint, sequence=sequence)


def main():
	load_from_disk()

	workers = []
	server = ThreadedTCPServer(('0.0.0.0', PORT), TCPHandler)

	def start_worker(fnc):
		workers.append(threading.Thread(target=fnc, daemon=True))
		workers[-1].start()

	logger.info(f'[p2p] listening on PORT {PORT}')
	start_worker(server.serve_forever)

	if get_peer_hostnames():
		logger.info(f'start initial block download from {len(get_peer_hostnames())} peers')
		send_to_peer(GetBlocksMsg(get_active_chain()[-1].id))
		get_ibd_done().wait(60.)

	start_worker(mine_forever)
	[w.join() for w in workers]


if __name__ == '__main__':
	from mini_core.wallet import init_wallet
	signing_key, verifying_key, my_address = init_wallet()
	main()


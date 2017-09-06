import logging
import os

from typing import Iterable, Union
from threading import RLock
from mini_core.block import Block
from mini_core.exceptions import BlockValidationError
from mini_core.mempool import mempool
from mini_core.transaction import Transaction, SignatureScript, TxIn, TxOut
from mini_core.utils import deserialize
from mini_core.utxo_set import add_to_utxo
from functools import wraps


CHAIN_PATH = os.environ.get('TC_CHAIN_PATH', 'chain.dat')

logger = logging.getLogger(__name__)

generic_block_params = {
    'version': 0,
    'prev_block_hash': None,
    'merkle_tree_hash': '688787d8ff144c502c7f5cffaafe2cc588d86079f9de88304c26b0cb99ce91c6',
    'timestamp': 1504563279,
    'bits': 24,
    'nonce': 86038336,
    'txns': [
        Transaction(
            txins=[
                TxIn(outpoint=None, signature=SignatureScript(
                    unlock_sig='0', unlock_pk=None), sequence=0)
            ],
            txouts=[
                TxOut(value=5000000, pubkey='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF')
            ]
        )
    ]
}

genesis_block = Block(**generic_block_params)

# highest proof of work
active_chain: Iterable[Block] = [genesis_block]

# side branches
side_branches: Iterable[Iterable[Block]] = []

orphan_blocks: Iterable[Block] = []

ACTIVE_CHAIN_IDX = 0

# Synchronize access to the active chain and side branches
chain_lock = RLock()


def set_active_chain(val: Iterable[Block]):
    """
    Should not be called outside of testing purpose
    """
    global active_chain
    active_chain = val


def get_active_chain() -> Iterable[Block]:
    return active_chain


def with_lock(lock):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorate


@with_lock(chain_lock)
def get_current_height():
    return len(active_chain)


@with_lock(chain_lock)
def txn_iterator(chain):
    return (
        (txn, block, height)
        for height, block in enumerate(chain) for txn in block.txns
    )


@with_lock(chain_lock)
def locate_block(block_hash: str, chain=None) -> (Block, int, int):
    chains = [chain] if chain else [active_chain, *side_branches]

    for chain_idx, chain in enumerate(chains):
        for height, block in enumerate(chain):
            if block.id == block_hash:
                return (block, height, chain_idx)
    return (None, None, None)


@with_lock(chain_lock)
def connect_block(block: Union[str, Block], doing_reorg=False) -> Union[None, Block]:
    """
    Accept a block and return the chain index we append it to.
    """
    from mini_core.validation import validate_block

    search_chain = active_chain if doing_reorg else None

    if locate_block(block.id, chain=search_chain)[0]:
        logger.debug(f'ignore block already seen: {block.id}')
        return None

    try:
        block, chain_idx = validate_block(block)
    except BlockValidationError as e:
        logger.exception(f'block {block.id} failed validation')
        if e.to_orphan:
            logger.info(f'saw orphan block {block.id}')
            orphan_blocks.append(e.to_orphan)
        return None

    # If validate_block returned a non-existent chain index, we're creating
    # a new side branch
    if chain_idx != ACTIVE_CHAIN_IDX and len(side_branches) < chain_idx:
        logger.info(
            f'creating a new side branch (idx {chain_idx})'
            f'for block {block.id}')
        side_branches.append([])

    logger.info(f'connecting block {block.id} to chain {chain_idx}')
    chain = (active_chain if chain_idx ==
             ACTIVE_CHAIN_IDX else side_branches[chain_idx-1])
    chain.append(block)

    # If we added to the active chain, perform upkeep on utxo_set and mempool
    if chain_idx == ACTIVE_CHAIN_IDX:
        for txn in block.txns:
            mempool.pop(txn.id, None)

            if not txn.is_coinbase:
                for txin in txn.txins:
                    rm_from_utxo(*txin.outpoint)
            for i, txout in enumerate(txn.txouts):
                add_to_utxo(txout, txn, i, txn.is_coinbase, len(chain))

    if (not doing_reorg and reorg_if_necessary()) or chain_idx == ACTIVE_CHAIN_IDX:
        from mini_core.proof_of_work import mine_interrupt
        mine_interrupt.set()
        logger.info(
            f'block accepted'
            f'height={len(active_chain) - 1} txns={len(block.txns)}'
        )

    import mini_core.networking as n
    for peer in n.peer_hostnames:
        send_to_peer(block, peer)

    return chain_idx


@with_lock(chain_lock)
def disconnect_block(block, chain=None):
    chain = chain or active_chain
    assert block == chain[-1], "Block being disconnected must be tip."

    for txn in blocks.txns:
        mempool[txn.id] = txn

        # Restore UTXO set to what it was before this block.
        for txin in txn.txins:
            if txin.outpoint: # account for degenerate coinbase txins.
                add_to_utxo(*find_txout_for_txin(txin, chain))
        for i in range(len(txn.txouts)):
            rm_from_utxo(txn.id, i)

    logger.info(f'block {block.id} disconnected')
    return chain.pop()


def find_txout_for_txin(txin, chain):
    txid, txout_idx = txin.outpoint

    for txn, block, height in txn_iterator(chain):
        if txn.id == txid:
            txout = txn.txouts[txout_idx]
            return (txout, txn, txout_idx, txn.is_coinbase, height)


@with_lock(chain_lock)
def reorg_if_necessary() -> bool:
    reorged = False
    frozen_side_branches = list(side_branches)

    # TODO should probably be using `chainwork` for the basis of comparison here.
    for branch_idx, chain in enumerate(frozen_side_branches, 1):
        fork_block, fork_idx, _ = locate_block(
            chain[0].prev_block_hash, active_chain)
        active_height = len(active_chain)
        branch_height = len(chain) + fork_idx

        if branch_height > active_height:
            logger.info(
                f"attempting reorg of idx {branch_idx} to active_chain: "
                f"new height of {branch_height} (vs. {active_height})"
            )
            reorged |= try_reorg(chain, branch_idx, fork_idx)

    return reorged


@with_lock(chain_lock)
def try_reorg(branch, branch_idx, fork_idx) -> bool:
    global side_branches

    def disconnect_to_fork():
        while active_chain[-1].id != fork_block.id:
            yield disconnect_block(active_chain[-1])

    old_active = list(disconnect_to_fork())[::-1]

    assert branch[0].prev_block_hash == active_chain[-1].id

    def rollback_reorg():
        logger.info(f'reorg of idx {branch_idx} to active_chain failed')
        list(disconnect_to_fork()) # force the generate to eval

        for block in old_active:
            assert connect_block(block, doing_reorg=True) == ACTIVE_CHAIN_IDX

    for block in branch:
        connected_idx = connect_block(block, doing_reorg=True)
        if connected_idx != ACTIVE_CHAIN_IDX:
            rollback_reorg()
            return False

    # Fix up side branches: remove new active, add old active.
    side_branches.pop(branch_idx - 1)
    side_branches.append(old_active)

    logger.info(f'chain reorg! New height: {len(active_chain)}, tip: {active_chain[-1].id}')
    return True


@with_lock(chain_lock)
def save_to_disk():
    with open(CHAIN_PATH, 'wb') as f:
        logger.info(f'saving chain with {len(active_chain)} blocks')
        f.write(encode_socket_data(list(active_chain)))


@with_lock(chain_lock)
def load_from_disk():
    if not os.path.isfile(CHAIN_PATH):
        return

    try:
        with open(CHAIN_PATH, 'rb') as f:
            msg_len = int(binascii.hexlify(f.read(4) or b'\x00'), 16)
            new_blocks = deserialize(f.read(msg_len))
            logger.info(
                r'loading chain from disk with {len(new_blocks)} block')
            for block in new_blocks:
                connect_block(block)
    except Exception as e:
        logger.exception('load chain failed, starting from genesis')

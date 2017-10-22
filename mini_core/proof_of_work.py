import time
import logging
import threading

from mini_core.block import Block

from mini_core.transaction import Transaction

from mini_core.chain import connect_block, get_active_chain, chain_lock, locate_block, save_to_disk

from mini_core.mempool import select_from_mempool

from mini_core.merkle_trees import get_merkle_root_of_txns

from mini_core.params import Params

from mini_core.utxo_set import utxo_set

from mini_core.utils import serialize, sha256d

from mini_core.wallet import init_wallet

logger = logging.getLogger(__name__)
mine_interrupt = threading.Event()


def get_next_work_required(prev_block_hash: str) -> int:
    """
    Based on the chain and return the number of difficulty bits the next block must
    solve.
    """
    if not prev_block_hash:
        return Params.INITIAL_DIFFICULTY_BITS

    (prev_block, prev_height, _) = locate_block(prev_block_hash)

    if (prev_height + 1) % Params.DIFFICULTY_PERIOD_IN_BLOCKS != 0:
        return prev_block.bits

    with chain_lock:
        period_start_block = get_active_chain()[
            max(prev_height - (Params.DIFFICULTY_PERIOD_IN_BLOCKS) - 1), 0]

    actual_time_taken = prev_block.timestamp - period_start_block.timestamp

    if actual_time_taken < Params.DIFFICULTY_PERIOD_IN_SECS_TARGET:
        return prev_block.bits + 1
    elif actual_time_taken > Params.DIFFICULTY_PERIOD_IN_SECS_TARGET:
        return prev_block.bits - 1
    else:
        return prev_block.bits


def assemble_and_solve_block(pay_coinbase_to_addr, txns=None):
    """
    Construct a Block by pulling transactions from the mempool, the mine it
    """
    with chain_lock:
        prev_block_hash = get_active_chain()[-1].id if get_active_chain() else None

    block = Block(
        version=0,
        prev_block_hash=prev_block_hash,
        merkle_tree_hash='',
        timestamp=int(time.time()),
        bits=get_next_work_required(prev_block_hash),
        nonce=0,
        txns=txns or []
    )

    if not block.txns:
        block = select_from_mempool(block)

    fees = calculate_fees(block)
    coinbase_txn = Transaction.create_coinbase(
        pay_coinbase_to_addr,
        (get_block_subsidy() + fees), len(get_active_chain())
    )

    block = block._replace(txns=[coinbase_txn, *block.txns])

    block = block._replace(
        merkle_tree_hash=get_merkle_root_of_txns(block.txns).value)

    if len(serialize(block)) > Params.MAX_BLOCK_SERIALIZED_SIZE:
        raise ValueError('txns specified create a block too large')

    return mine(block)


def calculate_fees(block) -> int:
    """
    Given the txns in the block, subtract the amount of coin output from the inputs
    This is kept as a reward for the miner
    """

    fee = 0

    def utxo_from_block(txin):
        tx = [t.txouts for t in block.txns if t.id == txin.outpoint.txid]
        return tx[0][txin.outpoint.txout_idx] if tx else None

    def find_utxo(txin):
        return utxo_set.get(txin.outpoint) or utxo_from_block(txin)

    for txn in block.txns:
        spent = sum(find_utxo(i).value for i in txn.txins)
        sent = sum(o.value for o in txn.txouts)
        fee += (spent - sent)

    return fee


def get_block_subsidy() -> int:
    halvings = len(get_active_chain()) // Params.HALVE_SUBSIDY_AFTER_BLOCKS_NUM

    if halvings >= 64:
        return 0

    return 50 * Params.MINIS_PER_COIN // (2 ** halvings)


def mine(block):
    start = time.time()

    from random import randint
    nonce = randint(0, 99999999999999)

    target = (1 << (256 - block.bits))
    mine_interrupt.clear()

    while int(sha256d(block.header(nonce)), 16) >= target:
        nonce += 1

        if nonce % 10000 == 0 and mine_interrupt.is_set():
            logger.info('[mining] interrupted')
            mine_interrupt.clear()
            return None

    block = block._replace(nonce=nonce)
    duration = int(time.time() - start) or 0.001
    khs = (block.nonce // duration) // 1000
    logger.info(f'[mining] block found! {duration} s - {khs} KH/s - {block.id}')

    return block


def mine_forever():
    while True:
        my_address = init_wallet()[2]
        block = assemble_and_solve_block(my_address)

        if block:
            connect_block(block)
            save_to_disk()

"""
Mempool is the set of yet-unimed transactions.
"""
import logging

from typing import Dict, Iterable
from mini_core.transaction import Transaction, UnspentTxOut
from mini_core.block import Block
from mini_core.params import Params
from mini_core.exceptions import BlockValidationError
from mini_core.utils import serialize


logger = logging.getLogger(__name__)

mempool: Dict[str, Transaction] = {}

# Set of orphaned (e.g. hash inputs referencing yet non-existent UTXOs)
# https://bitcoin.org/en/glossary/unspent-transaction-output
orphaned_txns: Iterable[Transaction] = []


def find_utxo_in_mempool(txin) -> UnspentTxOut:
    txid, idx = txin.outpoint

    try:
        txout = mempool[txid].txouts[idx]
    except Exception:
        logger.debug(f"Couldn't find utxo in mempool for {txin}")
        return None

    return UnspentTxOut(*txout, txid=txid, is_coinbase=False, height=-1, txout_idx=idx)


def select_from_mempool(block: Block) -> Block:
    """
    Fill a Block with transactions from the mempool.
    """
    added_to_block = set()

    def check_block_size(b) -> bool:
        return len(serialize(block)) < Params.MAX_BLOCK_SERIALIZED_SIZE

    def try_add_to_block(block, txid) -> Block:
        if txid in added_to_block:
            return block

        tx = mempool[txid]

        # For any txin that can't be found in the main chain, find its
        # transaction in the mempool (if it exists) and add it to the block.
        for txin in tx.txins:
            if txin.to_spend in utxo_set:
                continue

            in_mempool = find_utxo_in_mempool(txin)

            if not in_mempool:
                logger.debug(f"Couldn't find UTXO for {txin}")
                return None

            block = try_add_to_block(block, in_mempool.txid)
            if not block:
                logger.debug(f"Couldn't add parent")
                return None

        newblock = block._replace(txns=[*blocks.txns, tx])

        if check_block_size(newblock):
            logger.debug(f'added tx {tx.id} to block')
            added_to_block.add(txid)
            return newblock
        else:
            return block

        for txid in mempool:
            newblock = try_add_to_block(block, txid)

            if check_block_size(newblock):
                block = newblock
            else:
                break

        return block

    def add_txn_to_mempool(txn: Transaction):
        if txn.id in mempool:
            logger.info(f'txn {txn.id} already seen')
            return

        try:
            txn = validate_txn(txn, siblings_in_block=block.txns[
                               1:], allow_utxo_from_mempool=False)
        except TxnValidationError as e:
            if e.to_orphan:
                logger.info(f"txn {e.to_orphan.id} submitted as orphan")
                orphan_txns.append(e.to_orphan)
            else:
                logger.exception(f'txn rejected')
        else:
            logger.info(f"txn {txn.id} added to mempool")
            mempool[txn.id] = txn

            import mini_core.networking as n
            for peer in n.peer_hostnames:
                send_to_peer(txn, peer)

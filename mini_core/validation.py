import binascii
import time
import ecdsa

from mini_core.block import Block

from mini_core.chain import ACTIVE_CHAIN_IDX, get_active_chain, get_current_height, with_lock, chain_lock, locate_block

from mini_core.exceptions import BlockValidationError, TxnValidationError, TxUnlockError

from mini_core.merkle_trees import get_merkle_root_of_txns
from mini_core.mempool import find_utxo_in_mempool
from mini_core.params import Params

from mini_core.proof_of_work import get_next_work_required

from mini_core.transaction import Transaction, UnspentTxOut

from mini_core.utils import sha256d, serialize, get_median_time_past

from mini_core.utxo_set import utxo_set, find_utxo_in_list

from mini_core.wallet import pubkey_to_address

from typing import Iterable


def validate_txn(txn: Transaction, as_coinbase: bool = False, siblings_in_block: Iterable[Transaction] = None, allow_utxo_from_mempool: bool = True):
    """
    Validate a single transaction. Used in various contexts, so the parameters facilitate difficult users
    """
    txn.validate_basics(as_coinbase=as_coinbase)
    available_to_spend = 0

    for i, txin in enumerate(txn.txins):
        utxo = utxo_set.get(txin.outpoint)

        if siblings_in_block:
            utxo = utxo or find_utxo_in_list(txin, siblings_in_block)

        if allow_utxo_from_mempool:
            utxo = utxo or find_utxo_in_mempool(txin)

        if not utxo:
            raise TxnValidationError(f'Could not find UTXO for TxIn[{i}] -- orphaning txn', to_orphan=txn)

        if utxo.is_coinbase and (get_current_height() - utxo.height) < Params.COINBASE_MATURITY:
            raise TxnValidationError(f'Coinbase UTXO not ready for spend')

        try:
            validate_signature_for_spend(txin, utxo, txn)
        except TxUnlockError:
            raise TxnValidationError(f'{txin} is not valid spend of {utxo}')

        available_to_spend += utxo.value

    if available_to_spend < sum(o.value for o in txn.txouts):
        raise TxnValidationError('Spend value is more than available')

    return txn


def validate_signature_for_spend(txin, utxo: UnspentTxOut, txn):
    pubkey_as_addr = pubkey_to_address(txin.signature.unlock_pk)
    verifying_key = ecdsa.VerifyingKey.from_string(
        txin.signature.unlock_pk, curve=ecdsa.SECP256k1)

    if pubkey_as_addr != utxo.pubkey:
        raise TxnUnlockError('Pubkey does not match')

    try:
        spend_msg = build_spend_message(
            txin.outpoint, txin.signature.unlock_pk, txin.sequence, txn.txouts)
        verifying_key.verify(txin.signature.unlock_sig, spend_msg)
    except Exception as e:
        logger.exception('Key verification failed')
        raise TxnUnlockError('Signature does not match')

    return True


def build_spend_message(outpoint, pk, sequence, txouts) -> bytes:
    """
    similar to: SIGHASH_ALL
    """
    return sha256d(
        serialize(outpoint) + str(sequence) +
        binascii.hexlify(pk).decode() + serialize(txouts)
    ).encode()


@with_lock(chain_lock)
def validate_block(block: Block) -> Block:
    # we can't have a block without transactions
    if not block.txns:
        raise BlockValidationError('txns empty')

    if block.timestamp - time.time() > Params.MAX_FUTURE_BLOCK_TIME:
        raise BlockValidationError('Block timestamp too far in the future')

    # bad pow
    if int(block.id, 16) > (1 << (256 - block.bits)):
        raise BlockValidationError('Block header does not satify bits')

    # first transaction must be the coinbase
    if [i for (i, tx) in enumerate(block.txns) if tx.is_coinbase] != [0]:
        raise BlockValidationError('First txn must be coinbase and no more')

    # validate the basics of each transaction
    try:
        for i, txn in enumerate(block.txns):
            txn.validate_basics(as_coinbase=(i == 0))
    except TxnValidationError:
        logger.exception(f'Transaction {txn} in {block} failed to validate')
        raise BlockValidationError('Invalid txn {txn.id}')

    # bad merklehash value, transactions invalid
    if get_merkle_root_of_txns(block.txns).value != block.merkle_tree_hash:
        raise BlockValidationError('Merkle Hash invalid')

    if block.timestamp <= get_median_time_past(11):
        raise BlockValidationError('timestamp too old')

    if not block.prev_block_hash and not get_active_chain():
        # genesis block
        prev_block_chain_idx = ACTIVE_CHAIN_IDX
    else:
        prev_block, prev_block_height, prev_block_chain_idx = locate_block(
            block.prev_block_hash)

        if not prev_block:
            raise BlockValidationError(f'prev block {block.prev_block_hash} not found in any chain', to_orphan=block)

        # No more validation for a block getting attached to a branch
        if prev_block_chain_idx != ACTIVE_CHAIN_IDX:
            return block, prev_block_chain_idx

        # Previous block found in the active chain, but isn't tip => new fork.
        elif prev_block != get_active_chain()[-1]:
            return block, prev_block_chain_idx + 1

    if get_next_work_required(block.prev_block_hash) != block.bits:
        raise BlockValidationError('bits is incorrect')

    for txn in block.txns[1:]:
        try:
            validate_txn(txn, siblings_in_block=block.txns[
                         1:], allow_utxo_from_mempool=False)
        except TxnValidationError:
            msg = f'{txn} failed to validate'
            logger.exception(msg)
            raise BlockValidationError(msg)

    return block, prev_block_chain_idx

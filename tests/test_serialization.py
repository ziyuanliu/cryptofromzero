import time

from mini_core.block import Block
from mini_core.transaction import OutPoint, Transaction, TxIn, TxOut, UnspentTxOut, SignatureScript
from mini_core.utils import deserialize, serialize


def test_serialization():
    outpoint1 = OutPoint(txid='coffee', txout_idx=0)
    outpoint2 = OutPoint(txid='coffee', txout_idx=0)
    txin1 = TxIn(outpoint=outpoint1, signature=SignatureScript(
        unlock_sig=b'sign', unlock_pk=b'bar'), sequence=1)
    txin2 = TxIn(outpoint=outpoint2, signature=SignatureScript(
        unlock_sig=b'sign', unlock_pk=b'bar'), sequence=2)

    txout = TxOut(value=101, pubkey='abcnddfjrwof123')
    txn1 = Transaction(txins=[txin1], txouts=[txout], locktime=0)
    txn2 = Transaction(txins=[txin2], txouts=[txout], locktime=0)

    block = Block(1, 'deadbeef', 'coffee', int(
        time.time()), 100, 100, [txn1, txn2])
    utxo = UnspentTxOut(*txout, txid=txn1.id, txout_idx=0,
                        is_coinbase=False, height=0)
    utxo_set = [utxo.outpoint, utxo]

    for obj in (outpoint1, outpoint2, txin1, txin2, txout, txn1, txn2, block, utxo, utxo_set):
        assert deserialize(serialize(obj)) == obj

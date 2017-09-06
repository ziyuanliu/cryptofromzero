from mini_core.transaction import OutPoint, Transaction, TxIn, TxOut, UnspentTxOut, SignatureScript
from mini_core.validation import build_spend_message


def test_build_spend_message():
    txout = TxOut(value=101, pubkey='1zz8w9')
    txin = TxIn(
        outpoint=OutPoint('c0ffee', 0),
        signature=SignatureScript(unlock_sig=b'oursig', unlock_pk=b'foo'),
        sequence=1
    )

    txn = Transaction(txins=[txin], txouts=[txout], locktime=0)
    spend_msg = build_spend_message(txin.outpoint, txin.signature.unlock_pk, txin.sequence, txn.txouts)

    assert spend_msg == b'2c162f2c05a771e52c01fda220073aa0665cc873193235bdb90359631720e7a5'

    # adding a new output to the txn creates a new spend message.

    txn.txouts.append(TxOut(value=1, pubkey='1zz'))
    assert build_spend_message(txin.outpoint, txin.signature.unlock_pk, txin.sequence, txn.txouts) != spend_msg

from mini_core.block import Block
from mini_core.chain import set_active_chain
from mini_core.transaction import OutPoint, Transaction, TxIn, TxOut, UnspentTxOut, SignatureScript
from mini_core.utils import get_median_time_past


def _dummy_block(**kwargs):
    defaults = dict(
        version=1, prev_block_hash='coffee', merkle_tree_hash='deadbeef',
        timestamp=1, bits=1, nonce=1, txns=[]
    )

    return Block(**{**defaults, **kwargs})


def test_get_median_time_past():
    set_active_chain([])

    assert get_median_time_past(10) == 0

    timestamps = [1, 30, 60, 90, 400]
    set_active_chain([_dummy_block(timestamp=t) for t in timestamps])

    assert get_median_time_past(1) == 400
    assert get_median_time_past(3) == 90
    assert get_median_time_past(2) == 90
    assert get_median_time_past(5) == 60

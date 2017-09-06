from mini_core.chain import ACTIVE_CHAIN_IDX, set_active_chain, connect_block, get_active_chain
from mini_core.mempool import mempool
from tests import chain1
from mini_core.utxo_set import utxo_set


def test_dependent_txns_in_single_block():
	set_active_chain([])
	mempool.clear()

	assert connect_block(chain1[0]) == ACTIVE_CHAIN_IDX
	assert connect_block(chain1[1]) == ACTIVE_CHAIN_IDX
	assert len(get_active_chain()) == 2
	assert len(utxo_set) == 2
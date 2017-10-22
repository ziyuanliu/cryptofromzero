import pytest

from mini_core.chain import ACTIVE_CHAIN_IDX, set_active_chain, set_side_branches, get_side_branches, connect_block, get_active_chain, reorg_if_necessary
from mini_core.transaction import Transaction, OutPoint, TxOut
from mini_core.wallet import pubkey_to_address
from mini_core.proof_of_work import assemble_and_solve_block
from mini_core.mempool import mempool, add_txn_to_mempool
from mini_core.exceptions import TxnValidationError
from mini_core.validation import validate_txn
from mini_core.utxo_set import utxo_set
from mini_core import make_txin

from tests import signing_key, chain1, chain2, chain3_faulty, _add_to_utxo_for_chain


def test_dependent_txns_in_single_block():
	set_active_chain([])
	mempool.clear()

	assert connect_block(chain1[0]) == ACTIVE_CHAIN_IDX
	assert connect_block(chain1[1]) == ACTIVE_CHAIN_IDX

	assert len(get_active_chain()) == 2
	assert len(utxo_set) == 2

	utxo1 = utxo_set[list(utxo_set.keys())[0]]
	txout1 = TxOut(value=901, pubkey=utxo1.pubkey)
	txin1 = make_txin(signing_key, utxo1.outpoint, txout1)
	txn1 = Transaction(txins=[txin1], txouts=[txout1], locktime=0)
 
	# Create a transaction that is depend on the yet-unconfirmed transaction above
	txout2 = TxOut(value=9001, pubkey=txout1.pubkey)
	txin2 = make_txin(signing_key, OutPoint(txn1.id, 0), txout2)
	txn2 = Transaction(txins=[txin2], txouts=[txout2], locktime=0)

	# assert that we don't accept this txn -- too early to spend the coinbase
	with pytest.raises(TxnValidationError) as excinfo:
		validate_txn(txn2)
		assert 'Spend value is more than available' in str(excinfo)

	connect_block(chain1[2])
	add_txn_to_mempool(txn1)
	assert txn1.id in mempool

	# In txn2, we're attemping to spend more than is available (9001 vs. 901).
	assert not add_txn_to_mempool(txn2)

	with pytest.raises(TxnValidationError) as excinfo:
		validate_txn(txn2)
		assert 'Spend value is more than available' in str(excinfo.value)


	# Recreate the transaction with an acceptable value
	txout2 = TxOut(value=901, pubkey=txout1.pubkey)
	txin2 = make_txin(signing_key, OutPoint(txn1.id, 0), txout2)
	txn2 = Transaction(txins=[txin2], txouts=[txout2], locktime=0)

	add_txn_to_mempool(txn2)
	assert txn2.id in mempool

	# block = assemble_and_solve_block(pubkey_to_address(signing_key.get_verifying_key().to_string()))

	# assert connect_block(block) == ACTIVE_CHAIN_IDX

	# assert get_active_chain()[-1] == block

	# assert block.txns[1:] == [txn1, txn2]
	# assert txn1.id not in mempool
	# assert txn2.id not in mempool

	# assert OutPoint(txn1.id, 0) not in utxo_set
	# assert OutPoint(txn2.id, 0) in utxo_set


def test_pubkey_address():
	assert pubkey_to_address(
		b'k\xd4\xd8M3\xc8\xf7h*\xd2\x16O\xe39a\xc9]\x18i\x08\xf1\xac\xb8\x0f'
        b'\x9af\xdd\xd1\'\xe2\xc2v\x8eCo\xd3\xc4\xff\x0e\xfc\x9eBzS\\=\x7f'
        b'\x7f\x1a}\xeen"\x9f\x9c\x17E\xeaMH\x88\xec\xf5F') == (
            '18kZswtcPRKCcf9GQsJLNFEMUE8V9tCJr')


def test_reorg():
	set_active_chain([])

	for block in chain1:
		assert connect_block(block) == ACTIVE_CHAIN_IDX

	set_side_branches([])
	mempool.clear()
	utxo_set.clear()
	_add_to_utxo_for_chain(get_active_chain())

	def assert_no_change():
		assert get_active_chain() == chain1
		assert mempool == {}
		assert [k.txid[:6] for k in utxo_set] == ['804da2', 'd961d7', '54b38d']

	assert len(utxo_set) == 3

	# No reorg necessary when side branches are empty
	assert not reorg_if_necessary()
	print(f'{[b.id for b in chain1]}')
	from mini_core.merkle_trees import get_merkle_root_of_txns
	print(f'{[get_merkle_root_of_txns(b.txns).value for b in chain2]}')
	# No reorg necessary when side branch is shorter than the main chain
	for block in chain2[1:2]:
		assert connect_block(block) == 1

	assert not reorg_if_necessary()
	assert get_side_branches() == [chain2[1:2]]
	assert_no_change()

	# No reorg necessary when side branch is as long as the main chain.
	assert connect_block(chain2[2]) == 1
	assert not reorg_if_necessary()
	assert get_side_branches() == [chain2[1:3]]
	assert_no_change()

	# No reorg necessary when side branch is a longer but invalid chain
	# Block doesn't connect to anything because it's invalid
	assert connect_block(chain3_faulty[3]) is None
	assert not reorg_if_necessary()

	# No change in side branches for an invalid block.
	assert get_side_branches() == [chain2[1:3]]
	assert_no_change()

	# Reorg necessary when a side branch is longer than the main chain
	assert connect_block(chain2[3]) == 1
	assert connect_block(chain2[4]) == 1

	# Chain1 was reorged into get_side_branches().
	assert [len(c) for c in get_side_branches()] == [2]
	assert [b.id for b in get_side_branches()[0]] == [b.id for b in chain1[1:]]
	assert get_side_branches() == [chain1[1:]]
	assert mempool == {}
	print(f'{[tx.txid[:6] for tx in utxo_set]}')
	assert [k.txid[:6] for k in utxo_set] == ['804da2', 'd961d7', '54b38d', '48f7f5', 'ac4700']












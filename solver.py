import random
import multiprocessing
from multiprocessing import Pool

from mini_core.block import Block
from mini_core.transaction import SignatureScript, Transaction, TxIn, TxOut


def pool_solver(rng):
    print(f"calculating range {rng}")
    for nonce in rng:
        b = Block(version=0, prev_block_hash='000000273d64c0b32fa8475004513d1e5f8335a718dc9bd6c99f60d5cf6f7175', merkle_tree_hash='5b9f0cb4023a18cd1de03c0035283965aa6b14ec72a5d9ce7b2a029a9afce47a', timestamp=1501827000, bits=24, nonce=nonce,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'4', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])

        if int(b.id, 16) <= (1 << (256-b.bits)):
            return nonce, b.id

    return None

pool = Pool(processes=multiprocessing.cpu_count())

interval = 1000000

rngs = list(range(start*interval, (start+1) * interval) for start in range(0, 600))
for retval in pool.imap_unordered(pool_solver, rngs):
	if retval:
		pool.close()
		pool.terminate()
		pool.join()
		print(retval)
	

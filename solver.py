import random
import multiprocessing
from multiprocessing import Pool

from mini_core.block import Block
from mini_core.transaction import SignatureScript, Transaction, TxIn, TxOut


def pool_solver(rng):
    print(f"calculating range {rng}")
    for nonce in rng:
        b = Block(version=0, prev_block_hash='000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3', merkle_tree_hash='031f45ad7b5ddf198f7dfa88f53c0262fb14c850c5c1faf506258b9dcad32aef', timestamp=1501826556, bits=24, nonce=nonce,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'2', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])

        if int(b.id, 16) <= (1 << (256-b.bits)):
            return nonce

    return None

pool = Pool(processes=multiprocessing.cpu_count())

interval = 1000000

rngs = list(range(start*interval, (start+1) * interval) for start in range(40, 60))
for retval in pool.imap_unordered(pool_solver, rngs):
	if retval:
		pool.close()
		pool.terminate()
		pool.join()
		print(retval)
	

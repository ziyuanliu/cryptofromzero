from mini_core.block import Block
from mini_core.transaction import SignatureScript, Transaction, TxIn, TxOut


chain1 = [
    # Block id:
    # 0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80
    Block(version=0, prev_block_hash=None, merkle_tree_hash='548b61957ff5fb0cb3d2c511f1a6e28460f0d7175eaa3058bfac986d37a72004', timestamp=1501821412, bits=24, nonce=2275359062, txns=[Transaction(txins=[
          TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'0', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF')], locktime=None)]),

    # Block id:
    # 000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3
    Block(version=0, prev_block_hash='0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80', merkle_tree_hash='509dd8d49774ddf72c24f83faa5a2e851da514103f53e6bec3df4ad5f83d8421', timestamp=1501826444, bits=24, nonce=5244659,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'1', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Block id:
    # 000000f9b679482f24902297fc59c745e759436ac95e93d2c1eff4d5dbd39e33
    Block(version=0, prev_block_hash='000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3', merkle_tree_hash='031f45ad7b5ddf198f7dfa88f53c0262fb14c850c5c1faf506258b9dcad32aef', timestamp=1501826556, bits=24, nonce=42447905,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'2', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])
]

chain2 = [
    # Block id:
    # 0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80
    Block(version=0, prev_block_hash=None, merkle_tree_hash='548b61957ff5fb0cb3d2c511f1a6e28460f0d7175eaa3058bfac986d37a72004', timestamp=1501821412, bits=24, nonce=2275359062, txns=[Transaction(txins=[
          TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'0', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF')], locktime=None)]),

    # Block id:
    # 000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3
    Block(version=0, prev_block_hash='0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80', merkle_tree_hash='509dd8d49774ddf72c24f83faa5a2e851da514103f53e6bec3df4ad5f83d8421', timestamp=1501826757, bits=24, nonce=5244659,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'1', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Block id:
    # 000000a1698495a3b125d9cd08837cdabffa192639588cdda8018ed8f5af3f8c
    Block(version=0, prev_block_hash='000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3', merkle_tree_hash='031f45ad7b5ddf198f7dfa88f53c0262fb14c850c5c1faf506258b9dcad32aef', timestamp=1501826872, bits=24, nonce=16925076,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'2', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Up until this point, we're same length as chain1.

    # This block is where chain3_faulty goes bad.
    # Block id:
    # 000000ef44dd5a56c89a43b9cff28e51e5fd91624be3a2de722d864ae4f6a853
    Block(version=0, prev_block_hash='000000a1698495a3b125d9cd08837cdabffa192639588cdda8018ed8f5af3f8c', merkle_tree_hash='dbf593cf959b3a03ea97bbeb7a44ee3f4841b338d5ceaa5705b637c853c956ef', timestamp=1501826949, bits=24, nonce=12052237,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'3', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Block id:
    Block(version=0, prev_block_hash='000000ef44dd5a56c89a43b9cff28e51e5fd91624be3a2de722d864ae4f6a853', merkle_tree_hash='a3a55fe5e9f9e5e3282333ac4d149fd186f157a3c1d2b2e04af78c20a519f6b9', timestamp=1501827000, bits=24, nonce=752898,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'4', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])
]

# Make this chain invalid.
chain3_faulty = list(chain2)
chain3_faulty[-2] = chain3_faulty[-2]._replace(nonce=1)

from mini_core.block import Block
from mini_core.transaction import SignatureScript, Transaction, TxIn, TxOut, OutPoint
from mini_core.validation import build_spend_message
import ecdsa


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
    # 0000009a67600e6c9fdad5a5aa420af45a23a092e1dcbc5e7e61aebc6cbbff66
    Block(version=0, prev_block_hash='000000d432bd0ec0a087a0d30a6e5c251116919bf91e195f1f9c3d4f3e3f0ba3', merkle_tree_hash='15c1faa633c048a3888619db00c446d167d15bb733cc0f5415e96211683531f3', timestamp=1501826556, bits=24, nonce=11288152,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'2', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])
]

chain2 = [
    # Block id:
    # 0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80
    Block(version=0, prev_block_hash=None, merkle_tree_hash='548b61957ff5fb0cb3d2c511f1a6e28460f0d7175eaa3058bfac986d37a72004', timestamp=1501821412, bits=24, nonce=2275359062, txns=[Transaction(txins=[
          TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'0', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF')], locktime=None)]),

    # Block id:
    # 0000003e2d6bc3a7c92aef8a8b622d47ce51fdff1257b7072ff974c660c8e7f6
    Block(version=0, prev_block_hash='0000009284177ad434618ded91f9f81fad78e0c26f77cffb5d9a406a8d4dab80', merkle_tree_hash='509dd8d49774ddf72c24f83faa5a2e851da514103f53e6bec3df4ad5f83d8421', timestamp=1501826757, bits=24, nonce=16491710,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'1', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Block id:
    # 0000005c770dbfeeb86b4defd739867a0424e65b005e70f7447207ac8b3bd53d
    Block(version=0, prev_block_hash='0000003e2d6bc3a7c92aef8a8b622d47ce51fdff1257b7072ff974c660c8e7f6', merkle_tree_hash='15c1faa633c048a3888619db00c446d167d15bb733cc0f5415e96211683531f3', timestamp=1501826872, bits=24, nonce=18352155,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'2', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Up until this point, we're same length as chain1.

    # This block is where chain3_faulty goes bad.
    # Block id:
    # 000000273d64c0b32fa8475004513d1e5f8335a718dc9bd6c99f60d5cf6f7175
    Block(version=0, prev_block_hash='0000005c770dbfeeb86b4defd739867a0424e65b005e70f7447207ac8b3bd53d', merkle_tree_hash='1e6fde3ce6523f3a61cfc21914012d85ab8c17c5bcd5e1e9a8633b151ee1ea2e', timestamp=1501826949, bits=24, nonce=32970614,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'3', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)]),

    # Block id:
    # 000000f6444b41fc1fc0bcc12f1fbc9120e72dfeecb1268b26127529b9a799cf
    Block(version=0, prev_block_hash='000000273d64c0b32fa8475004513d1e5f8335a718dc9bd6c99f60d5cf6f7175', merkle_tree_hash='5b9f0cb4023a18cd1de03c0035283965aa6b14ec72a5d9ce7b2a029a9afce47a', timestamp=1501827000, bits=24, nonce=5473045,
          txns=[Transaction(txins=[TxIn(outpoint=None, signature=SignatureScript(unlock_sig=b'4', unlock_pk=None), sequence=0)], txouts=[TxOut(value=5000000000, pubkey='1Piq91dFUqSb7tdddCWvuGX5UgdzXeoAwA')], locktime=None)])
]

# Make this chain invalid.
chain3_faulty = list(chain2)
chain3_faulty[-2] = chain3_faulty[-2]._replace(nonce=1)


def _add_to_utxo_for_chain(chain):
    from mini_core.utxo_set import add_to_utxo
    for block in chain:
        for tx in block.txns:
            for i, txout in enumerate(tx.txouts):
                add_to_utxo(txout, tx, i, tx.is_coinbase, len(chain))

# signing key
signing_key = ecdsa.SigningKey.from_string(
    b'\xf1\xad2y\xbf\xa2x\xabn\xfbO\x98\xf7\xa7\xb4\xc0\xf4fOzX\xbf\xf6\\\xd2\xcb-\x1d:0 \xa7',
    curve=ecdsa.SECP256k1)


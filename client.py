#!/usr/bin/env python3
"""
tinychain client

Usage:
  client.py balance [options] [--raw]
  client.py send [options] <addr> <val>
  client.py status [options] <txid> [--csv]

Options:
  -h --help            Show help
  -w, --wallet PATH    Use a particular wallet file (e.g. `-w ./wallet2.dat`)
  -n, --node HOSTNAME  The hostname of node to use for RPC (default: localhost)
  -p, --port PORT      Port node is listening on (default: 8888)

"""

import logging
import os
import socket

from docopt import docopt

from mini_core import make_txin
from mini_core.wallet import init_wallet
from mini_core.chain import txn_iterator
from mini_core.networking import GetActiveChainMsg, GetMempoolMsg, encode_socket_data, read_all_from_socket, GetUTXOsMsg
from mini_core.transaction import Transaction, TxOut


logging.basicConfig(
	level=getattr(logging, os.environ.get('TC_LOG_LEVEL', 'INFO')),
	format='[%(asctime)s][%(module)s:%(lineno)d] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def main(args):
	wallet = args.get('--wallet')
	args['signing_key'], args['verifying_key'], args['my_addr'] = (init_wallet(wallet))
	
	if args['--port']:
		send_msg.port = args['--port']

	if args['--node']:
		send_msg.node_hostname = args['--node']

	if args['balance']:
		get_balance(args)
	elif args['send']:
		send_value(args)
	elif args['status']:
		txn_status(args)


def get_balance(args):
	"""
	Get the balance of a given address
	"""
	val = sum(i.value for i in find_utxos_for_address(args))
	print(val)


def txn_status(args):
	"""
	Get the status of a transaction

	Prints [status],[containing block_id],[height mined]
	"""
	txid = args['<txid>']
	mempool = send_msg(GetMempoolMsg())

	if txid in mempool:
		print(f'{txid}:in mempool')
		return

	chain = send_msg(GetActiveChainMsg())

	for tx, block, height in txn_iterator(chain):
		if tx.id == txid:
			print(f'Mined in {block.id} at height {height}')
			return

	print(f'Not found')


def send_value(args):
	"""
	Send value to some address.
	"""

	val, to_addr, sk = int(args['<val>']), args['<addr>'], args['signing_key']
	selected = set()
	my_utxos = set(sorted(find_utxos_for_address(args), key=lambda i: (i.value, i.height)))

	for utxo in my_utxos:
		selected.add(utxo)
		if sum(i.value for i in selected) > val:
			break

	txout = TxOut(value=val, pubkey=to_addr)
	txn = Transaction(
		txins=[make_txin(sk, coin.outpoint, txout) for coin in selected], txouts=[txout])

	logger.info(f'built txn {txn}')
	logger.info(f'broadcast txn {txn.id}')
	send_msg(txn)


def send_msg(data: bytes, node_hostname=None, port=None):
	node_hostname = getattr(send_msg, 'node_hostname', 'localhost')
	port = getattr(send_msg, 'port', 8888)

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((node_hostname, port))
		s.sendall(encode_socket_data(data))
		return read_all_from_socket(s)


def find_utxos_for_address(args: dict):
	utxo_set = dict(send_msg(GetUTXOsMsg()))
	return [u for u in utxo_set.values() if u.pubkey == args['my_addr']]


if __name__ == '__main__':
    main(docopt(__doc__, version='tinychain client 0.1'))

import logging
import os

from mini_core.block import Block
from mini_core.transaction import OutPoint, Transaction, TxIn, TxOut, UnspentTxOut, SignatureScript


logging.basicConfig(
    level=getattr(logging, os.environ.get('TC_LOG_LEVEL', 'INFO')),
    format='[%(asctime)s][%(module)s:%(lineno)d] %(levelname)s %(message)s')

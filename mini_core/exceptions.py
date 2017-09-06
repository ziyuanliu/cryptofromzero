from mini_core.transaction import Transaction
from mini_core.block import Block


class TxUnlockError(Exception):
    pass


class TxnValidationError(Exception):

    def __init__(self, *args, to_orphan: Transaction = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_orphan = to_orphan


class BlockValidationError(Exception):

    def __init__(self, *args, to_orphan: Block = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_orphan = to_orphan

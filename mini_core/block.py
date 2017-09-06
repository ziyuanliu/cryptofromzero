from typing import NamedTuple, Iterable
from mini_core.transaction import Transaction
from mini_core.utils import sha256d


class Block(NamedTuple):
    """
    https://bitcoin.org/en/glossary/block

    """

    # a version integer
    version: int

    # a hash of the previous block's header
    prev_block_hash: str

    # a hash of the Merkle Tree containing all txns
    merkle_tree_hash: str

    # An UNIX timestamp of creation time
    timestamp: int

    # The difficulty target
    bits: int

    # The value that's incremented in an attempt to get the block header to a
    # value below its bits
    nonce: int

    txns: Iterable[Transaction]

    def header(self, nonce=None) -> str:
        return (
            f"{self.version}{self.prev_block_hash}{self.merkle_tree_hash}"
            f"{self.timestamp}{self.bits}{nonce or self.nonce}"
        )

    @property
    def id(self) -> str:
        return sha256d(self.header())

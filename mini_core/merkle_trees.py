from typing import NamedTuple, Iterable, Tuple
from functools import lru_cache
from mini_core.utils import sha256d, _chunks


class MerkleNode(NamedTuple):
    value: str
    children: Iterable = None


def get_merkle_root_of_txns(txns):
    return get_merkle_root(*[t.id for t in txns])


@lru_cache(maxsize=1024)
def get_merkle_root(*leaves: Tuple[str]) -> MerkleNode:
    """
    Builds a Merkle Tree and returns the root given some leaf values.
    """
    if len(leaves) % 2 == 1:
        leaves = leaves + (leaves[-1],)

    def find_root(nodes):
        newlevel = [
            MerkleNode(value=sha256d(i1.value + i2.value), children=[i1, i2])
            for [i1, i2] in _chunks(nodes, 2)
        ]
        return find_root(newlevel) if len(newlevel) > 1 else newlevel[0]

    return find_root([MerkleNode(sha256d(l)) for l in leaves])

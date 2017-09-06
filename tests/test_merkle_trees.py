from mini_core.merkle_trees import get_merkle_root
from mini_core.utils import sha256d


def test_merkle_trees():
    root = get_merkle_root('foo', 'bar')
    foo_hash = sha256d('foo')
    bar_hash = sha256d('bar')

    assert root
    assert root.value == sha256d(foo_hash + bar_hash)
    assert root.children[0].value == foo_hash
    assert root.children[1].value == bar_hash

    root = get_merkle_root('foo', 'bar', 'baz')
    baz_hash = sha256d('baz')

    assert root
    assert len(root.children) == 2
    assert root.children[0].value == sha256d(foo_hash + bar_hash)
    assert root.children[1].value == sha256d(baz_hash + baz_hash)

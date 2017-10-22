import hashlib
import json
import binascii

from typing import get_type_hints, Iterable, Mapping, Union


def sha256d(s: Union[str, bytes]) -> str:
    """
    double SHA256 hash
    """

    if not isinstance(s, bytes):
        s = s.encode()

    return hashlib.sha256(hashlib.sha256(s).digest()).hexdigest()


def get_median_time_past(num_last_blocks: int) -> int:
    from mini_core.chain import get_active_chain

    last_n_blocks = get_active_chain()[::-1][:num_last_blocks]

    if not last_n_blocks:
        return 0

    return last_n_blocks[len(last_n_blocks) // 2].timestamp


def _chunks(l, n) -> Iterable[Iterable]:
    return (l[i:i + n] for i in range(0, len(l), n))


def serialize(obj) -> str:
    """NamedTuple-flavored serialization to JSON."""
    def contents_to_primitive(o):
        if hasattr(o, '_asdict'):
            o = {**o._asdict(), '_type': type(o).__name__}
        elif isinstance(o, (list, tuple)):
            return [contents_to_primitive(i) for i in o]
        elif isinstance(o, bytes):
            return binascii.hexlify(o).decode()
        elif not isinstance(o, (dict, bytes, str, int, type(None))):
            raise ValueError(f"Can't serialize {o}")

        if isinstance(o, Mapping):
            for k, v in o.items():
                o[k] = contents_to_primitive(v)

        return o

    return json.dumps(
        contents_to_primitive(obj), sort_keys=True, separators=(',', ':'))


def deserialize(serialized: str) -> object:
    """NamedTuple-flavored serialization from JSON."""
    import mini_core
    gs = vars(mini_core)

    def contents_to_objs(o):
        if isinstance(o, list):
            return [contents_to_objs(i) for i in o]
        elif not isinstance(o, Mapping):
            return o

        _type = gs[o.pop('_type', None)]
        bytes_keys = {
            k for k, v in get_type_hints(_type).items() if v == bytes}

        for k, v in o.items():
            o[k] = contents_to_objs(v)

            if k in bytes_keys:
                o[k] = binascii.unhexlify(o[k]) if o[k] else o[k]

        return _type(**o)

    return contents_to_objs(json.loads(serialized))

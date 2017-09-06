
import os
import yaml

PARAMETERS_PATH = os.path.join(os.path.dirname(__file__), 'parameters.yml')


def load_defaults(cls):
    defaults = yaml.load(open(PARAMETERS_PATH))
    defaults = {**defaults, **dict(
        MAX_MONEY=defaults['MINIS_PER_COIN']*defaults['TOTAL_COINS'],
        DIFFICULTY_PERIOD_IN_BLOCKS=defaults['DIFFICULTY_PERIOD_IN_SECS_TARGET'] *
        defaults['TIME_BETWEEN_BLOCKS_IN_SECS_TARGET']
    )}

    for k, v in defaults.items():
        setattr(cls, k, v)

    return cls


@load_defaults
class Params:
    pass

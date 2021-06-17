import copy
from dataclasses import dataclass

from coqpit.coqpit import Coqpit


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10


def test_copying():
    config = SimpleConfig()

    config_new = config.copy()
    config_new.val_a = 1234
    assert config.val_a != config_new.val_a

    config_new = copy.copy(config)
    config_new.val_a = 4321
    assert config.val_a != config_new.val_a

    config_new = copy.deepcopy(config)
    config_new.val_a = 4321
    assert config.val_a != config_new.val_a

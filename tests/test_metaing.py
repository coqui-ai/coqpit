import dataclasses
from coqpit.coqpit import Coqpit


class SimpleConstructConfig(Coqpit):
    a: int = 20


def test_copying():
    assert dataclasses.is_dataclass(SimpleConstructConfig())

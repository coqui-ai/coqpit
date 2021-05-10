from dataclasses import dataclass

from coqpit.coqpit import Coqpit


@dataclass
class CoqpitA(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"
    val_same: float = 10.21


@dataclass
class CoqpitB(Coqpit):
    val_e: int = 257
    val_f: float = -10.21
    val_g: str = "Coqpit is really great!"
    val_same: int = 25  # duplicate fields are override by the merged Coqpit class.


@dataclass
class Reference(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"
    val_e: int = 257
    val_f: float = -10.21
    val_g: str = "Coqpit is really great!"
    val_same: int = 10.21  # duplicate fields are override by the merged Coqpit class.


def test_config_merge():
    coqpit_ref = Reference()
    coqpita = CoqpitA()
    coqpitb = CoqpitB()
    coqpitb.merge(coqpita)
    print(coqpitb.val_a)
    print(coqpitb.pprint())

    assert coqpit_ref.val_a == coqpitb.val_a
    assert coqpit_ref.val_b == coqpitb.val_b
    assert coqpit_ref.val_c == coqpitb.val_c
    assert coqpit_ref.val_e == coqpitb.val_e
    assert coqpit_ref.val_f == coqpitb.val_f
    assert coqpit_ref.val_g == coqpitb.val_g
    assert coqpit_ref.val_same == coqpitb.val_same

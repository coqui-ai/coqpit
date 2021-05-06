import os
from dataclasses import dataclass

from coqpit.coqpit import Coqpit, check_argument


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


if __name__ == "__main__":
    file_path = os.path.dirname(os.path.abspath(__file__))
    coqpita = CoqpitA()
    coqpitb = CoqpitB()
    coqpitb.merge(coqpita)
    print(coqpitb.val_a)
    print(coqpitb.pprint())

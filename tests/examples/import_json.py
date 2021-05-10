import os
from dataclasses import dataclass
from typing import List

from coqpit import Coqpit


@dataclass
class Person(Coqpit):
    name: str = None
    age: int = None


@dataclass
class Group(Coqpit):
    name: str = None
    size: int = None
    people: List[Person] = None


if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_config.json")
    config = Group()
    config.load_json(file_path)
    config.pprint()

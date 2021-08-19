import os
from dataclasses import dataclass, field
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


@dataclass
class Reference(Coqpit):
    name: str = "Coqpit"
    size: int = 3
    people: List[Person] = field(
        default_factory=lambda: [
            Person(name="Eren", age=11),
            Person(name="Geren", age=12),
            Person(name="Ceren", age=15),
        ]
    )


def assert_equal(a: Reference, b: Reference):
    assert len(a) == len(b)
    assert a.name == b.name
    assert a.size == b.size
    assert a.people[0].name == b.people[0].name
    assert a.people[1].name == b.people[1].name
    assert a.people[2].name == b.people[2].name
    assert a.people[0].age == b.people[0].age
    assert a.people[1].age == b.people[1].age
    assert a.people[2].age == b.people[2].age


def test_serizalization():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_serialization.json")

    ref_config = Reference()
    ref_config.save_json(file_path)

    new_config = Group()
    new_config.load_json(file_path)
    new_config.pprint()

    assert_equal(ref_config, new_config)


def test_serizalization_fileobject():
    """Test serialization to and from file-like objects instead of paths"""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_serialization_file.json")

    ref_config = Reference()
    with open(file_path, "w") as f:
        ref_config.save_json(f)

    new_config = Group()
    with open(file_path, "r") as f:
        new_config.load_json(f)
    new_config.pprint()

    assert_equal(ref_config, new_config)

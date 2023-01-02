import os
from dataclasses import field
from typing import List

from coqpit import Coqpit, CoqpitTypeError


class Person(Coqpit):
    name: str = None
    age: int = None


class Group(Coqpit):
    name: str = None
    size: int = None
    people: List[Person] = None


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


def test_serizalization():
    # pylint: disable=unsubscriptable-object
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_serialization.json")

    ref_config = Reference()
    ref_config.save_json(file_path)

    new_config = Group()
    new_config.load_json(file_path)
    new_config.pprint()

    # check values
    assert len(ref_config) == len(new_config)
    assert ref_config.name == new_config.name
    assert ref_config.size == new_config.size
    assert ref_config.people[0].name == new_config.people[0].name
    assert ref_config.people[1].name == new_config.people[1].name
    assert ref_config.people[2].name == new_config.people[2].name
    assert ref_config.people[0].age == new_config.people[0].age
    assert ref_config.people[1].age == new_config.people[1].age
    assert ref_config.people[2].age == new_config.people[2].age


def test_faulty_deserialization():
    """Try to load a json file with a type mismatch"""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_faulty_deserialization.json")

    try:
        ref_config = Reference()
        ref_config.load_json(file_path)
        assert False, "Should have failed"
    except CoqpitTypeError as e:
        pass
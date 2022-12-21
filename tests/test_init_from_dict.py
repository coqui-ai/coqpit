from dataclasses import dataclass, field
from typing import List

from coqpit import Coqpit


@dataclass
class Person(Coqpit):
    name: str = None
    age: int = None


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
    people_ids: List[int] = field(default_factory=lambda: [1, 2, 3])


@dataclass
class WithRequired(Coqpit):
    name: str


def test_new_from_dict():
    ref_config = Reference(name="Fancy", size=3**10, people=[Person(name="Anonymous", age=42)])

    new_config = Reference.new_from_dict(
        {"name": "Fancy", "size": 3**10, "people": [{"name": "Anonymous", "age": 42}]}
    )

    # check values
    assert len(ref_config) == len(new_config)
    assert ref_config.name == new_config.name
    assert ref_config.size == new_config.size
    assert ref_config.people[0].name == new_config.people[0].name
    assert ref_config.people[0].age == new_config.people[0].age

    try:
        WithRequired.new_from_dict({})
    except ValueError as e:
        assert "Missing required field" in e.args[0]

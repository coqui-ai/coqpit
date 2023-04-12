import sys
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple

import pytest
from typing_extensions import TypedDict

from coqpit import Coqpit
from coqpit.coqpit import check, check_dataclass, is_error, is_typeddict


def test_tuple():
    assert not is_error(check((1, 2, 3), Tuple[int, ...]))
    assert is_error(check((1, "b"), Tuple[int, ...]))


def test_set():
    assert is_error(check({"foo", "bar", 1}, Set[str]))


def test_str():
    assert is_error(check("foo", List[str]))


def test_callable():
    assert is_error(check(1, Callable))


@dataclass
class B:
    a: int = 0
    b: Dict[str, int] = field(default_factory=dict)


@dataclass
class A:
    a: int = 0
    b: str = ""
    c: B = field(default_factory=B)


class C(Coqpit):
    a: int = 0
    b: Dict[str, int] = field(default_factory=dict)


def test_error():
    a = A("foo")
    err = check_dataclass(a, A)
    assert is_error(err)
    assert "a" in err.path


def test_error_dataclass():
    a = A(c=B(a="foo"))
    err = check_dataclass(a, A)
    assert is_error(err)
    assert "c" in err.path


def test_error_dict_value():
    a = A(c=B(b={"foo": "bar"}))
    err = check_dataclass(a, A)
    assert is_error(err)
    assert "c" in err.path
    assert "b" in err.path
    assert "foo" in err.path


def test_error_dict_key():
    a = A(c=B(b={1: 1}))
    err = check_dataclass(a, A)
    assert is_error(err)
    assert "c" in err.path
    assert "b" in err.path
    assert 1 not in err.path


def test_bool():
    assert is_error(check(1, bool))
    assert not is_error(check(1, int))

    assert not is_error(check(False, bool))
    assert is_error(check(False, int))


class ENUM(Enum):
    a = "a"


def test_enum():
    assert is_error(check("a", ENUM))
    assert not is_error(check(ENUM.a, ENUM))


class TD(TypedDict):
    a: str
    b: int
    c: Optional["TD"]


class TDPartial(TypedDict, total=False):
    a: str
    b: int
    c: Optional["TDPartial"]


class TDList(TypedDict):
    a: int
    b: List[TDPartial]


@pytest.mark.parametrize(
    "ty,value",
    [
        (TDList, {"a": 1, "b": [{"a": "1"}]}),
        (TD, {"a": "foo", "b": 1, "c": None}),
        (TDPartial, {"a": "foo"}),
        (TDPartial, {}),
        (TDPartial, {"c": {"c": {"c": {"c": {"c": {}}}}}}),
        (
            TD,
            {
                "a": "foo",
                "b": 1,
                "c": {"a": "bar", "b": 1, "c": {"a": "foo", "b": 2, "c": None}},
            },
        ),
    ],
)
def test_typeddict(ty, value):
    assert not is_error(check(value, ty))


@pytest.mark.parametrize(
    "ty,value",
    [
        (TD, {"a": "foo", "b": 1}),
        (TD, {"a": 1}),
        (TDPartial, {"c": {"c": {"c": {"c": {"c": {"a": 10}}}}}}),
        (
            TD,
            {
                "a": "foo",
                "b": 1,
                "c": {"a": "bar", "b": 1, "c": {"a": 1, "b": 2, "c": None}},
            },
        ),
    ],
)
def test_typeddict_error(ty, value):
    assert is_error(check(value, ty))


if sys.version_info >= (3, 8, 0):

    class XTD(typing.TypedDict):
        a: int

    def test_is_typeddict():
        assert is_typeddict(XTD)

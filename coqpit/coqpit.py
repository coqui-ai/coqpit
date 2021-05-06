import argparse
import json
import os
from dataclasses import MISSING as _MISSING
from dataclasses import Field, asdict, dataclass, fields, is_dataclass
from pprint import pprint
from typing import Any, Generic, List, TypeVar, Union, _GenericAlias, get_type_hints

T = TypeVar("T")
MISSING: Any = "???"


class _NoDefault(Generic[T]):
    pass


NoDefaultVar = Union[_NoDefault[T], T]
no_default: NoDefaultVar = _NoDefault()


def _serialize(x):
    """Pick the right serialization for the datatype of the given input.

    Args:
        x (object): input object.

    Returns:
        object: serialized object.
    """
    if isinstance(x, dict):
        return {k: _serialize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_serialize(xi) for xi in x]
    if isinstance(x, Serializable) or issubclass(type(x), Serializable):
        return x.serialize()
    if isinstance(x, type) and issubclass(x, Serializable):
        return x.serialize(x)
    return x


def _deserialize(x, field_type):
    """Pick the right desrialization for the give object

    Args:
        x (object): object to be deserialized.
        field_type (type): expected type after deserialization.

    Returns:
        object: deserialized object
    """
    if is_dict(field_type):
        out_dict = {}
        for k, v in x.items():
            if v is None:  # if {'key':None}
                out_dict[k] = None
            else:
                out_dict[k] = _deserialize(v, type(v))
        return out_dict
    elif is_list(field_type):
        if hasattr(field_type, "__args__"):
            if len(field_type.__args__) > 1:
                raise ValueError(" [!] Coqpit does not support multi-type hinted 'List'")
            field_arg = field_type.__args__[0]
            return [_deserialize(xi, field_arg) for xi in x]
        else:
            return x
    elif is_union(field_type):
        for arg in field_type.__args__:
            # stop after first matching type in Union
            try:
                x = _deserialize(x, arg)
                break
            except ValueError:
                pass
        return x
    elif issubclass(field_type, Serializable):
        return field_type().deserialize(x)
    elif is_common_type(field_type):
        return x
    else:
        raise ValueError(f" [!] '{type(x)}' value type does not match '{field_type}' field type.")


def is_common_type(type: Any) -> bool:
    """Check if the input type is one of the common types (int, float, str).

    Args:
        type (typing.Any): input type to check.

    Returns:
        bool: True if input type is one of `int, float, str`.
    """
    return isinstance(type(), (int, float, str))


def is_list(type: Any) -> bool:
    """Check if the input type is `list`

    Args:
        type (typing.Any): input type.

    Returns:
        bool: True if input type is `list`
    """
    try:
        return type is list or type.__origin__ is list
    except AttributeError:
        return False


def is_dict(type: Any) -> bool:
    """Check if the input type is `list`

    Args:
        type (typing.Any): input type.

    Returns:
        bool: True if input type is `list`
    """
    try:
        return type is dict or type.__origin__ is dict
    except AttributeError:
        return False


def is_union(type: Any) -> bool:
    """Check if the input type is `Union`.

    Args:
        type (typing.Any): input type.

    Returns:
        bool: True if input type is `Union`
    """
    try:
        return safe_issubclass(type.__origin__, Union)
    except AttributeError:
        return False


def safe_issubclass(cls, classinfo) -> bool:
    """Check if the input type is a subclass of the given class.

    Args:
        cls (type): input type.
        classinfo (type): parent class.

    Returns:
        bool: True if the input type is a subclass of the given class
    """
    try:
        r = issubclass(cls, classinfo)
    except Exception:
        return cls is classinfo
    else:
        return r


def _default_value(x: Field):
    """Return the default value of the input Field.

    Args:
        x (Field): input Field.

    Returns:
        object: default value of the input Field.
    """
    if x.default != MISSING:
        return x.default
    elif x.default_factory != _MISSING:
        return x.default_factory()
    else:
        return x.default


def _is_optional_field(field) -> bool:
    """Check if the input field is optional.

    Args:
        field (Field): input Field to check.

    Returns:
        bool: True if the input field is optional.
    """
    return isinstance(field.type, _GenericAlias) and type(None) in getattr(field.type, "__args__")


def my_get_type_hints(
    cls,
):
    """Custom `get_type_hints` dealing with https://github.com/python/typing/issues/737

    Returns:
        [dataclass]: dataclass to get the type hints of its fields.
    """
    r_dict = {}
    for base in cls.__class__.__bases__:
        if base == object:
            break
        r_dict.update(my_get_type_hints(base))
    r_dict.update(get_type_hints(cls))
    return r_dict


@dataclass
class Serializable:
    """Gives serialization ability to any inheriting dataclass."""

    def __post_init__(self):
        self._validate_contracts()
        for key, value in self.__dict__.items():
            if value is no_default:
                raise TypeError(f"__init__ missing 1 required argument: '{key}'")

    def _validate_contracts(self):
        dataclass_fields = fields(self)

        for field in dataclass_fields:

            value = getattr(self, field.name)

            if value is None:
                if not _is_optional_field(field):
                    raise TypeError(f"{field.name} is not optional")

            contract = field.metadata.get("contract", None)

            if contract is not None:
                if value is not None and not contract(value):
                    raise ValueError(f"break the contract for {field.name}, {self.__class__.__name__}")

    def validate(self):
        """validate if object can serialize / deserialize correctly."""
        self._validate_contracts()
        if self != self.__class__.deserialize(json.loads(json.dumps(self.serialize()))):
            raise ValueError("could not be deserialized with same value")

    def to_dict(self) -> dict:
        """Transform serializable object to dict."""
        fields = fields(self)
        o = {}
        for field in fields:
            o[field.name] = getattr(self, field.name)
        return o

    def serialize(self) -> dict:
        """Serialize object to be json serializable representation."""
        if not is_dataclass(self):
            raise TypeError("need to be decorated as dataclass")

        dataclass_fields = fields(self)

        o = {}

        for field in dataclass_fields:
            value = getattr(self, field.name)
            value = _serialize(value)
            o[field.name] = value
        return o

    def deserialize(self, data: dict) -> "Serializable":
        """Parse input dictionary and desrialize its fields to a dataclass.

        Returns:
            self: deserialized `self`.
        """
        if not isinstance(data, dict):
            raise ValueError()
        data = data.copy()
        init_kwargs = {}
        for field in fields(self):
            # if field.name == 'dataset_config':
            if field.name not in data:
                init_kwargs[field.name] = vars(self)[field.name]
                continue
            value = data.get(field.name, _default_value(field))
            if value is None:
                init_kwargs[field.name] = value
                continue
            if value == MISSING:
                raise ValueError("deserialized with unknown value for {} in {}".format(field.name, self.__name__))
            value = _deserialize(value, field.type)
            init_kwargs[field.name] = value
        for k, v in init_kwargs.items():
            setattr(self, k, v)
        return self


# ---------------------------------------------------------------------------- #
#                        Argument Parsing from `argparse`                      #
# ---------------------------------------------------------------------------- #


def _get_help(field):
    try:
        field_help = field.metadata["help"]
    except KeyError:
        field_help = ""
    return field_help


def _init_argparse(
    parser,
    field_name,
    field_type,
    field_value,
    field_help,
    arg_prefix="",
    help_prefix="",
):
    if field_value is None and not is_common_type(field_type):
        # if the field type not int, flot or str, do not add it to the arguments
        return parser
    arg_prefix = field_name if arg_prefix == "" else f"{arg_prefix}.{field_name}"
    help_prefix = field_help if help_prefix == "" else f"{help_prefix} - {field_help}"
    if isinstance(field_type, dict):
        # TODO: currently I don't need it
        NotImplemented
    elif is_list(field_type):
        # TODO: We need a more clear help msg for lists.
        if len(field_type.__args__) > 1:
            raise ValueError(" [!] Coqpit does not support multi-type hinted 'List'")
        list_field_type = field_type.__args__[0]
        if field_value is None:
            # if the list is None, assume insertion of a new value/object to the list[0]
            # parser = _init_argparse(parser,
            #                         '0.',
            #                         list_field_type,
            #                         list_field_type(),
            #                         field_help='',
            #                         help_prefix=f'insert a new {list_field_type} to index 0 - {help_prefix} - ',
            #                         arg_prefix=f'{arg_prefix}.')
            # TODO: it complicates parsing argparse
            NotImplemented
        else:
            # if a list is defined, just enable editing the values from argparse
            # TODO: allow inserting a new value/obj to the end of the list.
            for idx, fv in enumerate(field_value):
                parser = _init_argparse(
                    parser,
                    str(idx),
                    list_field_type,
                    fv,
                    field_help="",
                    help_prefix=f"{help_prefix} - ",
                    arg_prefix=f"{arg_prefix}",
                )
    elif is_union(field_type):
        # TODO: currently I don't know how to handle Union type on argparse
        NotImplemented
    elif issubclass(field_type, Serializable):
        return field_value.init_argparse(parser, arg_prefix=arg_prefix, help_prefix=help_prefix)
    elif is_common_type(field_type):
        parser.add_argument(
            f"--coqpit.{arg_prefix}",
            default=field_value,
            type=field_type,
            help=f"Coqpit Field: {help_prefix}",
        )
    else:
        raise NotImplementedError(f" [!] '{field_type}' is not supported by arg_parser. Please file a bug report.")
    return parser


# ---------------------------------------------------------------------------- #
#                               Main Coqpit Class                              #
# ---------------------------------------------------------------------------- #


@dataclass
class Coqpit(Serializable):
    """Coqpit base class to be inherited by any future Coqpit dataclasses.
    It enables serializing/deserializing a dataclass to/from a json file, plus some semi-dynamic type and value check.
    Note that it does not support all datatypes and likely to fail in some special cases.
    """

    _initialized = False

    def _is_initialized(self):
        """Check if Coqpit is initialized. Useful to prevent running some aux functions
        at the initialization when no attribute has been defined."""
        return "_initialized" in vars(self) and self._initialized

    def __setattr__(self, name: str, value: Any) -> None:
        if self._is_initialized() and issubclass(type(value), Coqpit):
            self.__fields__[name].type = type(value)
        return super().__setattr__(name, value)

    def __set_fields(self):
        """Create a list of fields defined at the object initialization"""
        self.__fields__ = {}  # pylint: disable=attribute-defined-outside-init
        for field in fields(self):
            self.__fields__[field.name] = field

    def __post_init__(self):
        self._initialized = True
        self.__set_fields()
        try:
            self.check_values()
        except AttributeError:
            pass

    def __getitem__(self, arg: str):
        """Access class attributes with ``[arg]``."""
        return asdict(self)[arg]

    def __getattribute__(self, arg: str):
        """Check if the mandatory field is defined when accessing it."""
        value = super(Coqpit, self).__getattribute__(arg)
        if isinstance(value, str) and value == "???":
            raise AttributeError(f" [!] MISSING field {arg} must be defined.")
        return value

    def merge(self, coqpits: Union["Coqpit", List["Coqpit"]]):
        """Merge a coqpit instance or a list of coqpit instances to self.
        Note that it does not pass the fields and overrides attributes with
        the last Coqpit instance in the given List.
        TODO: find a way to merge instances with all the class internals.

        Args:
            coqpits (Union[Coqpit, List[Coqpit]]): coqpit instance or list of instances to be merged.
        """

        def _merge(coqpit):
            self.__dict__.update(coqpit.__dict__)
            self.__annotations__.update(coqpit.__annotations__)
            self.__dataclass_fields__.update(coqpit.__dataclass_fields__)

        if isinstance(coqpits, list):
            for coqpit in coqpits:
                _merge(coqpit)
        else:
            _merge(coqpits)

    def check_values(self):
        pass

    def has(self, arg: str) -> bool:
        return arg in vars(self)

    def update(self, new: dict, allow_new=False) -> None:
        """Update Coqpit fields by the input ```dict```.

        Args:
            new (dict): dictionary with new values.
            allow_new (bool, optional): allow new fields to add. Defaults to False.
        """
        for key, value in new.items():
            if allow_new:
                setattr(self, key, value)
            else:
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise KeyError(f" [!] No key - {key}")

    def pprint(self) -> None:
        """Print Coqpit fields in a format."""
        pprint(asdict(self))

    def to_dict(self) -> dict:
        # return asdict(self)
        return self.serialize()

    def from_dict(self, data: dict) -> None:
        self = self.deserialize(data)

    def to_json(self) -> str:
        """Returns a JSON string representation."""
        return json.dumps(asdict(self), indent=4)

    def save_json(self, file_name: str) -> None:
        """Save Coqpit to a json file.

        Args:
            file_name (str): path to the output json file.
        """
        with open(file_name, "w", encoding="utf8") as f:
            json.dump(asdict(self), f, indent=4)

    def load_json(self, file_name: str) -> None:
        """Load a json file and update matching config fields with type checking.
        Non-matching parameters in the json file are ignored.

        Args:
            file_name (str): path to the json file.

        Returns:
            Coqpit: new Coqpit with updated config fields.
        """
        with open(file_name, "r", encoding="utf8") as f:
            input_str = f.read()
            dump_dict = json.loads(input_str)
        # TODO: this looks stupid 💆
        self = self.deserialize(dump_dict)  # pylint: disable=self-cls-assignment
        self.check_values()

    def parse_args(self, args: argparse.Namespace) -> None:
        """Update config values from argparse arguments with some meta-programming ✨.

        Args:
            args (namespace): argeparse namespace as an output of ```argparse.parse_arguments()```.

        Returns:
            Coqpit: new config object with updated values.
        """
        if isinstance(args, argparse.Namespace):
            args_dict = vars(args)
        elif isinstance(args, list):
            # overriding values from .parse_known_args()
            args_dict = dict([*zip(args[::2], args[1::2])])
        for k, v in args_dict.items():
            if k.replace("--", "").startswith("coqpit") and "." in k:
                _, k = k.split(".", 1)
                names = k.split(".")
                cmd = "self"
                for name in names:
                    if str.isnumeric(name):
                        cmd += f"[{name}]"
                    else:
                        cmd += f".{name}"
                try:
                    exec(cmd)  # pylint: disable=exec-used
                except (TypeError, AttributeError) as e:
                    raise Exception(f" [!] '{k}' not exist to override from argparse.") from e

                if v is None:
                    cmd += "= None"
                elif isinstance(v, str):
                    cmd += f"= '{v}'"
                else:
                    cmd += f"= {v}"

                exec(cmd)  # pylint: disable=exec-used
        self.check_values()

    def init_argparse(self, parser: argparse.ArgumentParser, arg_prefix="", help_prefix="") -> argparse.ArgumentParser:
        """Pass Coqpit fields as argparse arguments. This allows to edit values through command-line.

        Args:
            parser (argparse.ArgumentParser): argparse.ArgumentParser instance.
            arg_prefix (str, optional): Prefix to be used for the argument name. Defaults to ''.
            help_prefix (str, optional): Prefix to be used for the argument description. Defaults to ''.

        Returns:
            argparse.ArgumentParser: parser instance with the new arguments.
        """
        class_fields = fields(self)
        field_value = None
        for field in class_fields:
            field_value = vars(self)[field.name]
            field_type = field.type
            field_help = _get_help(field)
            _init_argparse(
                parser,
                field.name,
                field_type,
                field_value,
                field_help,
                arg_prefix,
                help_prefix,
            )
        return parser


def check_argument(
    name,
    c,
    is_path: bool = False,
    prerequest: str = None,
    enum_list: list = None,
    max_val: float = None,
    min_val: float = None,
    restricted: bool = False,
    alternative: str = None,
    allow_none: bool = True,
) -> None:
    """Simple type and value checking for Coqpit.
    It is intended to be used under ```__post_init__()``` of config dataclasses.

    Args:
        name (str): name of the field to be checked.
        c (dict): config dictionary.
        is_path (bool, optional): if ```True``` check if the path is exist. Defaults to False.
        prerequest (list or str, optional): a list of field name that are prerequestedby the target field name.
            Defaults to ```[]```.
        enum_list (list, optional): list of possible values for the target field. Defaults to None.
        max_val (float, optional): maximum possible value for the target field. Defaults to None.
        min_val (float, optional): minimum possible value for the target field. Defaults to None.
        restricted (bool, optional): if ```True``` the target field has to be defined. Defaults to False.
        alternative (str, optional): a field name superceding the target field. Defaults to None.
        allow_none (bool, optional): if ```True``` allow the target field to be ```None```. Defaults to False.


    Example:
        >>> num_mels = 5
        >>> check_argument('num_mels', c, restricted=True, min_val=10, max_val=2056)
        >>> fft_size = 128
        >>> check_argument('fft_size', c, restricted=True, min_val=128, max_val=4058)
    """
    # check if None allowed
    if allow_none and c[name] is None:
        return
    if not allow_none:
        assert c[name] is not None, f" [!] None value is not allowed for {name}."
    # check if restricted and it it is check if it exists
    if isinstance(restricted, bool) and restricted:
        assert name in c.keys(), f" [!] {name} not defined in config.json"
    # check prerequest fields are defined
    if isinstance(prerequest, list):
        assert any(
            f not in c.keys() for f in prerequest
        ), f" [!] prequested fields {prerequest} for {name} are not defined."
    else:
        assert (
            prerequest is None or prerequest in c.keys()
        ), f" [!] prequested fields {prerequest} for {name} are not defined."
    # check if the path exists
    if is_path:
        assert os.path.exists(c[name]), " [!] {c[name]} not exist."
    # skip the rest if the alternative field is defined.
    if alternative in c.keys() and c[alternative] is not None:
        return
    # check value constraints
    if name in c.keys():
        if max_val is not None:
            assert c[name] <= max_val, f" [!] {name} is larger than max value {max_val}"
        if min_val is not None:
            assert c[name] >= min_val, f" [!] {name} is smaller than min value {min_val}"
        if enum_list is not None:
            assert c[name].lower() in enum_list, f" [!] {name} is not a valid value"

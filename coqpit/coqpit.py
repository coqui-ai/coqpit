import os
import json
from pprint import pprint
from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import get_type_hints, Any


def check_argument(name,
                   c,
                   is_path=False,
                   prerequest=None,
                   enum_list=None,
                   max_val=None,
                   min_val=None,
                   restricted=False,
                   alternative=None,
                   allow_none=False):
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

        def __post_init__(self,):
            '''Check config fields'''
            c = asdict(self)
            check_argument('num_mels', c, restricted=True, min_val=10, max_val=2056)
            check_argument('fft_size', c, restricted=True, min_val=128, max_val=4058)
    """
    # check if restricted and it it is check if it exists
    if isinstance(restricted, bool) and restricted:
        assert name in c.keys(), f' [!] {name} not defined in config.json'
    # check prerequest fields are defined
    if isinstance(prerequest, list):
        assert any([f not in c.keys() for f in prerequest]), f" [!] prequested fields {prerequest} for {name} are not defined."
    else:
        assert prerequest is None or prerequest in c.keys(), f" [!] prequested fields {prerequest} for {name} are not defined."
    # check if the path exists
    if is_path:
        assert os.path.exists(c[name]), " [!] {c[name]} not exist."
    # skip the rest if the alternative field is defined.
    if alternative in c.keys() and c[alternative] is not None:
        return
    # check if None allowed
    if allow_none and c[name] is None:
        return
    if not allow_none:
        assert c[name] is not None, f" [!] None value is not allowed for {name}."
    # check value constraints
    if name in c.keys():
        if max_val is not None:
            assert c[name] <= max_val, f' [!] {name} is larger than max value {max_val}'
        if min_val is not None:
            assert c[name] >= min_val, f' [!] {name} is smaller than min value {min_val}'
        if enum_list is not None:
            assert c[name].lower() in enum_list, f' [!] {name} is not a valid value'


def my_get_type_hints(cls):  # handle this python bug https://github.com/python/typing/issues/737
    r_dict = {}
    for base in  cls.__class__.__bases__:
        if base == object:
            break
        r_dict.update(my_get_type_hints(base))
    r_dict.update(get_type_hints(cls))
    return r_dict


def _decode_dataclass(cls, dump_dict, cls_type=None):
    """Parse the input dict and assign values to ```cls``` for the matching keywords to fields.

    Args:
        dump_dict (dict): dictionary with new field values.
        cls_type (type, optional): type of the cls object to enable type cheking for non-initialized Coqpit sub-fields.
            Defaults to None.

    Raises:
        ValueError: if input value type and the field type do not match.

    Returns:
        Coqpit(): a new Coqpit object with updated values.
    """
    dump_dict = {} if dump_dict is None else dump_dict
    cls = cls_type() if cls is None else cls
    init_kwargs = {}
    types = my_get_type_hints(cls)
    for field in fields(cls):
        if field.name not in dump_dict:
            continue

        field_value = dump_dict[field.name]

        field_type = types[field.name]
        if field_value is None:
            init_kwargs[field.name] = field_value
            continue

        if is_dataclass(field_type):
            if is_dataclass(field_value):
                value = field_value
            else:
                value = _decode_dataclass(vars(cls)[field.name], field_value, field_type)

            init_kwargs[field.name] = value
        else:
            if isinstance(field_value, field_type):
                init_kwargs[field.name] = field_value
            else:
                raise ValueError()

        # overwrite values in dataclass
        cls.update(init_kwargs)
    return cls


@dataclass
class Coqpit:
    """Base Coqpit dataclass to be inherited by custom dataclasses intended to be used for project configuration.
    It provides export, import abilities to and from json files. You can also update dataclass values from
    ```argparse``` namespace that enables updating dataclass values from commandline arguments.
    """

    def __setattr__(self, name: str, value: Any) -> None:
        """Run type checking for every new value assignment"""
        types = my_get_type_hints(self)
        type_annot = types[name]
        # allow None without type checking
        if value is not None:
            # type checking for list dict values against List, Dict typings.
            if isinstance(value, (list, dict)):
                type_origin = type_annot.__origin__
                type_args = type_annot.__args__
                if not isinstance(value, type_origin) or not (len(value) > 0 and isinstance(value[0], type_args[0])):
                    raise ValueError(f" [!] Value type {type(value)} is not same with the field type {types[name]}")
            else:
                # compare value type with field type allowing None as value
                if not isinstance(value, types[name]):
                    raise ValueError(f" [!] Value type {type(value)} is not same with the field type {types[name]}")
        self.__dict__[name] = value
        # run other checks too. TODO: call only for updated field
        self.__post_init__()

    def update(self, new):
        """Update Coqpit fields by the input ```dict```.

        Args:
            new (dict): dictionary with new values.
        """
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise KeyError(f' [!] No key - {key}')

    def pprint(self):
        """Print Coqpit fields in a format.
        """
        pprint(asdict(self))

    def _type_check(self, func):
        def with_type_check(self):
            r = func()
            self.__post_init__()
            return r
        return with_type_check

    def to_json(self):
        return json.dumps(asdict(self))

    def save_json(self, file_name):
        """Save Coqpit to a json file.

        Args:
            file_name (str): path to the output json file.
        """
        with open(file_name, 'w', encoding='utf8') as f:
            json.dump(asdict(self), f)

    def load_json(self, file_name):
        """Load a json file and update matching config fields with type checking.
        Non-matching parameters in the json file are ignored.

        Args:
            file_name (str): path to the json file.

        Returns:
            Coqpit: new Coqpit with updated config fields.
        """
        with open(file_name, 'r', encoding='utf8') as f:
            input_str = f.read()
            dump_dict = json.loads(input_str)
        self = _decode_dataclass(self, dump_dict)
        self.__post_init__()

    @classmethod
    def _parse_argparse(cls, args_dict):
        """Parse argsparse dict and convert arguments with dot notation to nested dictionaries

        Args:
            args_dict (dict): dictionary with dot notation keys.

        Returns:
            dict: dictionary in which dot notation keywords are converted to nested dictionary entries.
        """
        new_dict = {}
        for k, v in args_dict.items():
            if '.' in k:
                new_key, rest = k.split('.', 1)
                o_dict = cls._parse_argparse({rest: v})
                new_dict[new_key] = o_dict
            else:
                new_dict[k] = v
        return new_dict

    def from_argparse(self, args):
        """Update config values from argparse arguments.

        Args:
            args (namespace): argeparse namespace as an output of ```argparse.parse_arguments()```.

        Returns:
            Coqpit: new config object with updated values.
        """
        args_dict = vars(args)
        args_dict = self._parse_argparse(args_dict)
        self = _decode_dataclass(self, args_dict)
        self.__post_init__()

import argparse
import json
import os
from abc import abstractmethod
from dataclasses import asdict, dataclass, fields, is_dataclass
from pprint import pprint
from typing import Any, get_type_hints


def check_argument(name,
                   c,
                   is_path:bool=False,
                   prerequest:str=None,
                   enum_list:list=None,
                   max_val:float=None,
                   min_val:float=None,
                   restricted:bool=False,
                   alternative:str=None,
                   allow_none:bool=True) -> None:
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


def my_get_type_hints(cls):  # handle this python issue https://github.com/python/typing/issues/737
    r_dict = {}
    for base in  cls.__class__.__bases__:
        if base == object:
            break
        r_dict.update(my_get_type_hints(base))
    r_dict.update(get_type_hints(cls))
    return r_dict


def _decode_dataclass(cls:dataclass, dump_dict:dict, cls_type=None) -> dataclass:
    """Decode the input dictionary to the dataclass.

    Args:
        cls (Dataclass): target dataclass to be parsed from the input dictionary.
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

    # check all the external fields exist in the cls
    for k in dump_dict:
        if k not in asdict(cls):
            raise KeyError(f" [!] '{k}' from the input file is not defined.")

    # import external values to the cls
    for field in fields(cls):

        # pass fields not defined in the input file.
        if field.name not in dump_dict:
            continue
        import_value = dump_dict[field.name]
        field_type = types[field.name]

        # if None just import the value
        if import_value is None:
            init_kwargs[field.name] = import_value
            continue

        if is_dataclass(field_type):
            # if the field is anothe dataclass run recursively.
            if is_dataclass(import_value):
                imported_value = import_value
            else:
                imported_value = _decode_dataclass(vars(cls)[field.name], import_value, field_type)
            init_kwargs[field.name] = imported_value
        elif '__origin__' in field_type.__dict__ :
            if field_type.__origin__ is list:
                # if the field is a list, import each item in the list.
                field_types_in_list = field_type.__args__
                if len(import_value) > len(field_types_in_list):
                    field_types_in_list *= len(import_value)
                imported_values = []
                for ft, v in zip(field_types_in_list, import_value):
                    if is_dataclass(ft):
                        if is_dataclass(v):
                            imported_value = v
                        else:
                            imported_value = _decode_dataclass(None, v, ft)
                        imported_values.append(imported_value)
                    else:
                        imported_value = v
                        imported_values.append(imported_value)
                init_kwargs[field.name] = imported_values
            else:
                raise ValueError(f' [!] Value type `{field_type.__origin__ }` is not supported.')
        else:
            # if no dataclass import the value
            if isinstance(import_value, field_type):
                init_kwargs[field.name] = import_value
            else:
                raise ValueError()

        # overwrite values in dataclass
        cls.update(init_kwargs)
    return cls


@dataclass
class Coqpit:
    '''Coqpit base class to be inherited by any future Coqpit dataclasses.
    It enables serializing/deserializing a dataclass to/from a json file, plus some semi-dynamic type and value check.
    Note that it does not support all datatypes and likely to fail in some special cases.
    '''

    def __setattr__(self, name: str, value: Any) -> None:
        """Run type checking for every new value assignment
        TODO: It is more than I can chew 😅"""
        # if inspect.isclass(value):
        super().__setattr__(name, value)
        # else:
        #     types = my_get_type_hints(self)
        #     type_annot = types[name]

        #     # allow None without type checking
        #     if value is not None:
        #         # type checking for list dict values against List, Dict typings.
        #         if isinstance(value, (list, dict)):
        #             type_origin = type_annot.__origin__
        #             type_args = type_annot.__args__
        #             if not isinstance(value, type_origin) or not (len(value) > 0 and isinstance(value[0], type_args[0])):
        #                 raise ValueError(f" [!] {name} Value type {type(value)} is not same with the field type {types[name]}")
        #         else:
        #             # compare value type with field type allowing None as value
        #             if not isinstance(value, types[name]):
        #                 try:
        #                     value = types[name](value)
        #                 except:
        #                     raise ValueError(f" [!] {name} Value type {type(value)} is not same with the field type {types[name]}")

        #     self.__dict__[name] = value
        #     # run other checks too. TODO: call only for updated field
        # self.check_values()

    def __set_fields(self):
        '''Create a list of fields defined at the object initialization'''
        self.__fields__ = asdict(self).keys()

    def __post_init__(self):
        self.__set_fields()
        try:
            self.check_values()
        except AttributeError:
            pass

    def __getitem__(self, arg:str):
        '''Access class attributes with ``[arg]``.'''
        return asdict(self)[arg]

    def check_values(self):
        pass

    def update(self, new:dict) -> None:
        """Update Coqpit fields by the input ```dict```.

        Args:
            new (dict): dictionary with new values.
        """
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise KeyError(f' [!] No key - {key}')

    def pprint(self) -> None:
        """Print Coqpit fields in a format.
        """
        pprint(asdict(self))

    def to_json(self) -> str:
        """Returns a JSON string representation."""
        return json.dumps(asdict(self))

    def save_json(self, file_name:str) -> None:
        """Save Coqpit to a json file.

        Args:
            file_name (str): path to the output json file.
        """
        with open(file_name, 'w', encoding='utf8') as f:
            json.dump(asdict(self), f)

    def load_json(self, file_name:str) -> None:
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
        self.check_values()

    @classmethod
    def _parse_argparse(cls, args_dict:dict) -> dict:
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

    def from_argparse(self, args:argparse.Namespace) -> None:
        """Update config values from argparse arguments.

        Args:
            args (namespace): argeparse namespace as an output of ```argparse.parse_arguments()```.

        Returns:
            Coqpit: new config object with updated values.
        """
        args_dict = vars(args)
        args_dict = self._parse_argparse(args_dict)
        self = _decode_dataclass(self, args_dict)
        self.check_values()

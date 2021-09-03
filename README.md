# 👩‍✈️ Coqpit

[![CI](https://github.com/coqui-ai/coqpit/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/coqui-ai/coqpit/actions/workflows/main.yml)

Simple, light-weight and no dependency config handling through python data classes with to/from JSON serialization/deserialization.

Currently it is being used by [🐸TTS](https://github.com/coqui-ai/TTS).
## ❔ Why I need this
What I need from a ML configuration library...

1. Fixing a general config schema in Python to guide users about expected values.

    Python is good but not universal. Sometimes you train a ML model and use it on a different platform. So, you
    need your model configuration file importable by other programming languages.

2. Simple dynamic value and type checking with default values.

    If you are a beginner in a ML project, it is hard to guess the right values for your ML experiment. Therefore it is important
    to have some default values and know what range and type of input are expected for each field.

4. Ability to decompose large configs.

    As you define more fields for the training dataset, data preprocessing, model parameters, etc., your config file tends
    to get quite large but in most cases, they can be decomposed, enabling flexibility and readability.

5. Inheritance and nested configurations.

    Simply helps to keep configurations consistent and easier to maintain.

6. Ability to override values from the command line when necessary.

    For instance, you might need to define a path for your dataset, and this changes for almost every run. Then the user
    should be able to override this value easily over the command line.

    It also allows easy hyper-parameter search without changing your original code. Basically, you can run different models
    with different parameters just using command line arguments.

7. Defining dynamic or conditional config values.

    Sometimes you need to define certain values depending on the other values. Using python helps to define the underlying
    logic for such config values.

8. No dependencies

    You don't want to install a ton of libraries for just configuration management. If you install one, then it
    is better to be just native python.

## 🚫 Limitations
- `Union` type dataclass fields cannot be parsed from console arguments due to the type ambiguity.
- `JSON` is the only supported serialization format, although the others can be easily integrated.
- `List`type with multiple item type annotations are not supported. (e.g. `List[int, str]`).
- `dict` fields are parsed from console arguments as JSON str without type checking. (e.g `--val_dict '{"a":10, "b":100}'`).
- `MISSING` fields cannot be avoided when parsing console arguments.

## 🔍 Examples

### 👉 Simple Coqpit
```python
import os
from dataclasses import asdict, dataclass, field

from coqpit import MISSING, Coqpit, check_argument


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_d: float = 10.21
    val_c: str = "Coqpit is great!"
    # mandatory field
    # raise an error when accessing the value if it is not changed. It is a way to define
    val_k: int = MISSING
    # optional field
    val_dict: dict = field(default_factory=lambda: {"val_aa": 10, "val_ss": "This is in a dict."})
    # list of list
    val_listoflist: List[List] = field(default_factory=lambda: [[1, 2], [3, 4]])
    val_listofunion: List[List[Union[str]]] = field(default_factory=lambda: [[1, 3], [1, "Hi!"]])

    def check_values(
        self,
    ):  # you can define explicit constraints on the fields using `check_argument()`
        """Check config fields"""
        c = asdict(self)
        check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument("val_c", c, restricted=True)


if __name__ == "__main__":
    file_path = os.path.dirname(os.path.abspath(__file__))
    config = SimpleConfig()

    # try MISSING class argument
    try:
        k = config.val_k
    except AttributeError:
        print(" val_k needs a different value before accessing it.")
    config.val_k = 1000

    # try serialization and deserialization
    print(config.serialize())
    print(config.to_json())
    config.save_json(os.path.join(file_path, "example_config.json"))
    config.load_json(os.path.join(file_path, "example_config.json"))
    print(config.pprint())

    # try `dict` interface
    print(*config)
    print(dict(**config))

    # value assignment by mapping
    config["val_a"] = -999
    print(config["val_a"])
    assert config.val_a == -999
```
### 👉 Serialization
```python
import os
from dataclasses import asdict, dataclass, field
from coqpit import Coqpit, check_argument
from typing import List, Union


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"

    def check_values(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_a', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_b', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_c', c, restricted=True)


@dataclass
class NestedConfig(Coqpit):
    val_d: int = 10
    val_e: int = None
    val_f: str = "Coqpit is great!"
    sc_list: List[SimpleConfig] = None
    sc: SimpleConfig = SimpleConfig()
    union_var: Union[List[SimpleConfig], SimpleConfig] = field(default_factory=lambda: [SimpleConfig(),SimpleConfig()])

    def check_values(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_d', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_e', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_f', c, restricted=True)
        check_argument('sc_list', c, restricted=True, allow_none=True)
        check_argument('sc', c, restricted=True, allow_none=True)


if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))
    # init 🐸 dataclass
    config = NestedConfig()

    # save to a json file
    config.save_json(os.path.join(file_path, 'example_config.json'))
    # load a json file
    config2 = NestedConfig(val_d=None, val_e=500, val_f=None, sc_list=None, sc=None, union_var=None)
    # update the config with the json file.
    config2.load_json(os.path.join(file_path, 'example_config.json'))
    # now they should be having the same values.
    assert config == config2

    # pretty print the dataclass
    print(config.pprint())

    # export values to a dict
    config_dict = config.to_dict()
    # crate a new config with different values than the defaults
    config2 = NestedConfig(val_d=None, val_e=500, val_f=None, sc_list=None, sc=None, union_var=None)
    # update the config with the exported valuess from the previous config.
    config2.from_dict(config_dict)
    # now they should be having the same values.
    assert config == config2
```


### 👉 ```argparse``` handling and parsing.
```python
import argparse
import os
from dataclasses import asdict, dataclass, field
from typing import List

from coqpit import Coqpit, check_argument
import sys


@dataclass
class SimplerConfig(Coqpit):
    val_a: int = field(default=None, metadata={'help': 'this is val_a'})


@dataclass
class SimpleConfig(Coqpit):
    val_req: str # required field
    val_a: int = field(default=10,
                       metadata={'help': 'this is val_a of SimpleConfig'})
    val_b: int = field(default=None, metadata={'help': 'this is val_b'})
    nested_config: SimplerConfig = SimplerConfig()
    mylist_with_default: List[SimplerConfig] = field(
        default_factory=lambda:
        [SimplerConfig(val_a=100),
         SimplerConfig(val_a=999)],
        metadata={'help': 'list of SimplerConfig'})

    # mylist_without_default: List[SimplerConfig] = field(default=None, metadata={'help': 'list of SimplerConfig'})  # NOT SUPPORTED YET!

    def check_values(self, ):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_a', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_b',
                       c,
                       restricted=True,
                       min_val=128,
                       max_val=4058,
                       allow_none=True)
        check_argument('val_req', c, restricted=True)


def main():
    # reference config that we like to match with the one parsed from argparse
    config_ref = SimpleConfig(val_req='this is different',
                              val_a=222,
                              val_b=999,
                              nested_config=SimplerConfig(val_a=333),
                              mylist_with_default=[
                                  SimplerConfig(val_a=222),
                                  SimplerConfig(val_a=111)
                              ])

    # create new config object from CLI inputs
    parsed = SimpleConfig.init_from_argparse()
    parsed.pprint()

    # check the parsed config with the reference config
    assert parsed == config_ref


if __name__ == '__main__':
    sys.argv.extend(['--coqpit.val_req', 'this is different'])
    sys.argv.extend(['--coqpit.val_a', '222'])
    sys.argv.extend(['--coqpit.val_b', '999'])
    sys.argv.extend(['--coqpit.nested_config.val_a', '333'])
    sys.argv.extend(['--coqpit.mylist_with_default.0.val_a', '222'])
    sys.argv.extend(['--coqpit.mylist_with_default.1.val_a', '111'])
    main()
```

### 🤸‍♀️ Merging coqpits
```python
import os
from dataclasses import dataclass
from coqpit import Coqpit, check_argument


@dataclass
class CoqpitA(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_d: float = 10.21
    val_c: str = "Coqpit is great!"


@dataclass
class CoqpitB(Coqpit):
    val_d: int = 25
    val_e: int = 257
    val_f: float = -10.21
    val_g: str = "Coqpit is really great!"


if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))
    coqpita = CoqpitA()
    coqpitb = CoqpitB()
    coqpitb.merge(coqpita)
    print(coqpitb.val_a)
    print(coqpitb.pprint())
```

## Development

Install the pre-commit hook to automatically check your commits for style and hinting issues:

```bash
$ python .pre-commit-2.12.1.pyz install
```

<img src="https://static.scarf.sh/a.png?x-pxid=cd0232a8-ead2-4f1f-87f5-0dd8ec33ee51" />

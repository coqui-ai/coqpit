import os
from dataclasses import asdict, dataclass, field
from typing import List, Union

from coqpit import Coqpit, check_argument


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"

    def check_values(
        self,
    ):
        """Check config fields"""
        c = asdict(self)
        check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument("val_c", c, restricted=True)


@dataclass
class NestedConfig(Coqpit):
    val_d: int = 10
    val_e: int = None
    val_f: str = "Coqpit is great!"
    sc_list: List[SimpleConfig] = None
    sc: SimpleConfig = SimpleConfig()
    union_var: Union[List[SimpleConfig], SimpleConfig] = field(default_factory=lambda: [SimpleConfig(), SimpleConfig()])

    def check_values(
        self,
    ):
        """Check config fields"""
        c = asdict(self)
        check_argument("val_d", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_e", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument("val_f", c, restricted=True)
        check_argument("sc_list", c, restricted=True, allow_none=True)
        check_argument("sc", c, restricted=True, allow_none=True)


if __name__ == "__main__":
    file_path = os.path.dirname(os.path.abspath(__file__))
    # init 🐸 dataclass
    config = NestedConfig()

    # save to a json file
    config.save_json(os.path.join(file_path, "example_config.json"))
    # load a json file
    config2 = NestedConfig(val_d=None, val_e=500, val_f=None, sc_list=None, sc=None, union_var=None)
    # update the config with the json file.
    config2.load_json(os.path.join(file_path, "example_config.json"))
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

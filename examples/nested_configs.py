import os
from dataclasses import asdict, dataclass, field
from coqpit.coqpit import Coqpit, check_argument
from typing import List


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

    def check_values(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_d', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_e', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_f', c, restricted=True)
        check_argument('sc_list', c, restricted=True, allow_none=True)
        check_argument('sc', c, restricted=True, allow_none=False)


if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))

    config = NestedConfig()
    config.save_json(os.path.join(file_path, 'example_config.json'))
    print(config.pprint())

    config.load_json(os.path.join(file_path, 'example_config.json'))
    print(config.pprint())

    config.sc_list = [SimpleConfig(), SimpleConfig()]
    print(config.pprint())

    print(config.to_json())

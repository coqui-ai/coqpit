

import argparse
import os
from dataclasses import asdict, dataclass, field
from typing import List

from coqpit.coqpit import Coqpit, check_argument


@dataclass
class SimplerConfig(Coqpit):
    val_a: int = None

@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"
    mylist: List[SimplerConfig] = field(default_factory=lambda: [SimplerConfig(), SimplerConfig()])

    def check_values(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_a', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_b', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_c', c, restricted=True)


if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))
    config = SimpleConfig()
    print(config.to_json())
    config.save_json(os.path.join(file_path, 'example_config.json'))
    config.load_json(os.path.join(file_path, 'example_config.json'))
    print(config.pprint())

    parser = argparse.ArgumentParser()
    parser.add_argument('--val_a', default=25)
    parser.add_argument('--coqpit.val_a', default=999)
    parser.add_argument('--coqpit.mylist.0.val_a', default=20)
    parser.add_argument('--coqpit.mylist.1.val_a', default=100)
    # parser.add_argument('--coqpit.val_z', default=999)  # raises AttributeError since 'val_z' is not defined above
    # parser.add_argument('--coqpit.mylist.2.val_a', default=100)  # raises IndexError since 'mylist' is size of 2
    args = parser.parse_args()

    config.from_argparse(args)
    config.pprint()

import argparse
import os
from dataclasses import asdict, dataclass, field
from typing import List

from coqpit.coqpit import Coqpit, check_argument
import sys

@dataclass
class SimplerConfig(Coqpit):
    val_a: int = field(default=None, metadata={'help': 'this is val_a'})


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = field(default=10,
                       metadata={'help': 'this is val_a of SimpleConfig'})
    val_b: int = field(default=None, metadata={'help': 'this is val_b'})
    val_c: str = "Coqpit is great!"
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
        check_argument('val_c', c, restricted=True)

def main():
    file_path = os.path.dirname(os.path.abspath(__file__))

    # initial config
    config = SimpleConfig()
    print(config.pprint())

    # reference config that we like to match with the config above
    config_ref = SimpleConfig(val_a=222, val_b=999, val_c='this is different', mylist_with_default=[SimplerConfig(val_a=222), SimplerConfig(val_a=111)])

    # create and init argparser with Coqpit
    parser = argparse.ArgumentParser()
    parser = config.init_argparse(parser)
    parser.print_help()
    args = parser.parse_args()

    # parse the argsparser
    config.from_argparse(args)
    config.pprint()
    # check the current config with the reference config
    assert config == config_ref



if __name__ == '__main__':
    sys.argv.extend(['--val_a', '222'])
    sys.argv.extend(['--val_b', '999'])
    sys.argv.extend(['--val_c', 'this is different'])
    sys.argv.extend(['--mylist_with_default.0.val_a', '222'])
    sys.argv.extend(['--mylist_with_default.1.val_a', '111'])
    main()

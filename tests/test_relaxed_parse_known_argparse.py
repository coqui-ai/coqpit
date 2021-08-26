from dataclasses import asdict, dataclass, field
from typing import List, Union

from coqpit.coqpit import Coqpit, check_argument


@dataclass
class SimplerConfig(Coqpit):
    val_a: int = field(default=None, metadata={"help": "this is val_a"})


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = field(default=10, metadata={"help": "this is val_a of SimpleConfig"})
    val_b: int = field(default=None, metadata={"help": "this is val_b"})
    val_c: Union[int, str] = None
    val_d: List[List] = None

    def check_values(
        self,
    ):
        """Check config fields"""
        c = asdict(self)
        check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)


def test_parse_argparse():
    unknown_args = ["--coqpit.arg_does_not_exist", "111"]
    args = []
    args.extend(["--coqpit.val_a", "222"])
    args.extend(["--coqpit.val_b", "999"])
    args.extend(unknown_args)

    # initial config
    config = SimpleConfig()
    print(config.pprint())

    # reference config that we like to match with the config above
    config_ref = SimpleConfig(val_a=222, val_b=999, val_c=None, val_d=None)

    # create and init argparser with Coqpit
    parser = config.init_argparse(relaxed_parser=True)
    parser.print_help()

    # parse the argsparser
    unknown = config.parse_known_args(args, relaxed_parser=True)
    config.pprint()
    # check the current config with the reference config
    assert config == config_ref
    assert unknown == unknown_args

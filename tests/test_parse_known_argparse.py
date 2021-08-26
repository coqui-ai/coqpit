from dataclasses import asdict, dataclass, field
from typing import List

from coqpit.coqpit import Coqpit, check_argument


@dataclass
class SimplerConfig(Coqpit):
    val_a: int = field(default=None, metadata={"help": "this is val_a"})


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = field(default=10, metadata={"help": "this is val_a of SimpleConfig"})
    val_b: int = field(default=None, metadata={"help": "this is val_b"})
    val_c: str = "Coqpit is great!"
    mylist_with_default: List[SimplerConfig] = field(
        default_factory=lambda: [SimplerConfig(val_a=100), SimplerConfig(val_a=999)],
        metadata={"help": "list of SimplerConfig"},
    )

    def check_values(
        self,
    ):
        """Check config fields"""
        c = asdict(self)
        check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument("val_c", c, restricted=True)


def test_parse_argparse():
    unknown_args = ["--coqpit.arg_does_not_exist", "111"]
    args = []
    args.extend(["--coqpit.val_a", "222"])
    args.extend(["--coqpit.val_b", "999"])
    args.extend(["--coqpit.val_c", "this is different"])
    args.extend(["--coqpit.mylist_with_default.0.val_a", "222"])
    args.extend(["--coqpit.mylist_with_default.1.val_a", "111"])
    args.extend(unknown_args)

    # initial config
    config = SimpleConfig()
    print(config.pprint())

    # reference config that we like to match with the config above
    config_ref = SimpleConfig(
        val_a=222,
        val_b=999,
        val_c="this is different",
        mylist_with_default=[SimplerConfig(val_a=222), SimplerConfig(val_a=111)],
    )

    # create and init argparser with Coqpit
    parser = config.init_argparse()
    parser.print_help()

    # parse the argsparser
    unknown = config.parse_known_args(args)
    config.pprint()
    # check the current config with the reference config
    assert config == config_ref
    assert unknown == unknown_args


def test_parse_edited_argparse():
    """calling `parse_known_argparse` after some modifications in the config values.
    `parse_known_argparse` should keep the modified values if not defined in argv"""

    unknown_args = ["--coqpit.arg_does_not_exist", "111"]
    args = []
    args.extend(["--coqpit.mylist_with_default.1.val_a", "111"])
    args.extend(unknown_args)

    # initial config with modified values
    config = SimpleConfig()
    config.val_a = 333
    config.val_b = 444
    config.val_c = "this is different"
    config.mylist_with_default[0].val_a = 777
    print(config.pprint())

    # reference config that we like to match with the config above
    config_ref = SimpleConfig(
        val_a=333,
        val_b=444,
        val_c="this is different",
        mylist_with_default=[SimplerConfig(val_a=777), SimplerConfig(val_a=111)],
    )

    # create and init argparser with Coqpit
    parser = config.init_argparse()
    parser.print_help()

    # parse the argsparser
    unknown = config.parse_known_args(args)
    config.pprint()
    # check the current config with the reference config
    assert config == config_ref
    assert unknown == unknown_args

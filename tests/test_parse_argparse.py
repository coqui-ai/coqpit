from dataclasses import asdict, dataclass, field
from typing import List

from coqpit.coqpit import Coqpit, check_argument


class SimplerConfig(Coqpit):
    val_a: int = field(default=None, metadata={"help": "this is val_a"})


class SimpleConfig(Coqpit):
    val_a: int = field(default=10, metadata={"help": "this is val_a of SimpleConfig"})
    val_b: int = field(default=None, metadata={"help": "this is val_b"})
    val_c: str = "Coqpit is great!"
    val_dict: dict = field(default_factory=lambda: {"val_a": 100, "val_b": 200, "val_c": 300})
    mylist_with_default: List[SimplerConfig] = field(
        default_factory=lambda: [SimplerConfig(val_a=100), SimplerConfig(val_a=999)],
        metadata={"help": "list of SimplerConfig"},
    )
    int_list: List[int] = field(default_factory=lambda: [1, 2, 3], metadata={"help": "int"})
    str_list: List[str] = field(default_factory=lambda: ["veni", "vidi", "vici"], metadata={"help": "str"})
    empty_int_list: List[int] = field(default=None, metadata={"help": "int list without default value"})
    empty_str_list: List[str] = field(default=None, metadata={"help": "str list without default value"})
    list_with_default_factory: List[str] = field(
        default_factory=list, metadata={"help": "str list with default factory"}
    )

    # mylist_without_default: List[SimplerConfig] = field(default=None, metadata={'help': 'list of SimplerConfig'})  # NOT SUPPORTED YET!

    def check_values(
        self,
    ):
        """Check config fields"""
        c = asdict(self)
        check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
        check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument("val_c", c, restricted=True)


def test_parse_argparse():
    args = []
    args.extend(["--coqpit.val_a", "222"])
    args.extend(["--coqpit.val_b", "999"])
    args.extend(["--coqpit.val_c", "this is different"])
    args.extend(["--coqpit.val_dict", '{"val_a": 10, "val_b":20}'])
    args.extend(["--coqpit.mylist_with_default.0.val_a", "222"])
    args.extend(["--coqpit.mylist_with_default.1.val_a", "111"])
    args.extend(["--coqpit.empty_int_list", "111", "222", "333"])
    args.extend(["--coqpit.empty_str_list", "[foo=bar]", "[baz=qux]", "[blah,p=0.5,r=1~3]"])
    args.extend(["--coqpit.list_with_default_factory", "blah"])
    args.extend(["--coqpit.str_list.0", "neci"])
    args.extend(["--coqpit.int_list.1", "4"])

    # initial config
    config = SimpleConfig()
    print(config.pprint())

    # reference config that we like to match with the config above
    config_ref = SimpleConfig(
        val_a=222,
        val_b=999,
        val_c="this is different",
        val_dict={"val_a": 10, "val_b": 20},
        mylist_with_default=[SimplerConfig(val_a=222), SimplerConfig(val_a=111)],
        empty_int_list=[111, 222, 333],
        empty_str_list=["[foo=bar]", "[baz=qux]", "[blah,p=0.5,r=1~3]"],
        str_list=["neci", "vidi", "vici"],
        int_list=[1, 4, 3],
        list_with_default_factory=["blah"],
    )

    # create and init argparser with Coqpit
    parser = config.init_argparse()
    parser.print_help()

    # parse the argsparser
    config.parse_args(args)
    config.pprint()
    # check the current config with the reference config
    assert config == config_ref


def test_boolean_parse():
    @dataclass
    class Config(Coqpit):
        boolean_without_default: bool = field()
        boolean_with_default: bool = field(default=False)

    args = [
        "--coqpit.boolean_without_default",
        "false",
        "--coqpit.boolean_with_default",
        "true",
    ]

    config_ref = Config(
        boolean_without_default=False,
        boolean_with_default=True,
    )

    config = Config(boolean_without_default=True)
    config.parse_args(args)

    assert config == config_ref

    args = [
        "--coqpit.boolean_without_default",
        "blargh",
        "--coqpit.boolean_with_default",
        "true",
    ]

    try:
        config.parse_args(args)
        assert False, "should not reach this"
    except:  # pylint: disable=bare-except
        pass


@dataclass
class ArgparseWithRequiredField(Coqpit):
    val_a: int


def test_argparse_with_required_field():
    args = ["--coqpit.val_a", "10"]
    try:
        c = ArgparseWithRequiredField()  # pylint: disable=no-value-for-parameter
        c.parse_args(args)
        assert False
    except TypeError:
        # __init__ should fail due to missing val_a
        pass

    c = ArgparseWithRequiredField.init_from_argparse(args)
    assert c.val_a == 10


def test_init_argparse_list_and_nested():
    @dataclass
    class SimplerConfig2(Coqpit):
        val_a: int = field(default=None, metadata={"help": "this is val_a"})

    @dataclass
    class SimpleConfig2(Coqpit):
        val_req: str  # required field
        val_a: int = field(default=10, metadata={"help": "this is val_a of SimpleConfig2"})
        val_b: int = field(default=None, metadata={"help": "this is val_b"})
        nested_config: SimplerConfig2 = SimplerConfig2()
        mylist_with_default: List[SimplerConfig2] = field(
            default_factory=lambda: [SimplerConfig2(val_a=100), SimplerConfig2(val_a=999)],
            metadata={"help": "list of SimplerConfig2"},
        )

        # mylist_without_default: List[SimplerConfig2] = field(default=None, metadata={'help': 'list of SimplerConfig2'})  # NOT SUPPORTED YET!

        def check_values(
            self,
        ):
            """Check config fields"""
            c = asdict(self)
            check_argument("val_a", c, restricted=True, min_val=10, max_val=2056)
            check_argument("val_b", c, restricted=True, min_val=128, max_val=4058, allow_none=True)
            check_argument("val_req", c, restricted=True)

    # reference config that we like to match with the one parsed from argparse
    config_ref = SimpleConfig2(
        val_req="this is different",
        val_a=222,
        val_b=999,
        nested_config=SimplerConfig2(val_a=333),
        mylist_with_default=[SimplerConfig2(val_a=222), SimplerConfig2(val_a=111)],
    )

    # create new config object from CLI inputs
    args = [
        "--coqpit.val_req",
        "this is different",
        "--coqpit.val_a",
        "222",
        "--coqpit.val_b",
        "999",
        "--coqpit.nested_config.val_a",
        "333",
        "--coqpit.mylist_with_default.0.val_a",
        "222",
        "--coqpit.mylist_with_default.1.val_a",
        "111",
    ]
    parsed = SimpleConfig2.init_from_argparse(args)
    parsed.pprint()

    # check the parsed config with the reference config
    assert parsed == config_ref

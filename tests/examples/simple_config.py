import os
from dataclasses import asdict, dataclass, field

from coqpit.coqpit import MISSING, Coqpit, check_argument


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_d: float = 10.21
    val_c: str = "Coqpit is great!"
    val_k: int = MISSING  # raise an error when accessing the value if it is not changed. It is a way to define
    # mandatory fields
    val_dict: dict = field(default_factory=lambda: {"val_aa": 10, "val_ss": "This is in a dict."})

    def check_values(
        self,
    ):  # you can define explitic constraints on the datacalss fields using `check_argument`
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
from dataclasses import asdict, dataclass
from coqpit.coqpit import Coqpit, check_argument


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_c: str = "Coqpit is great!"

    def __post_init__(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_a', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_b', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_c', c, restricted=True)


if __name__ == '__main__':
    config = SimpleConfig()
    print(config.to_json())
    config.save_json('example_config.json')
    config.load_json('example_config2.json')
    print(config.to_json())

    # this outputs
    # >>> AssertionError:  [!] val_a is smaller than min value 10

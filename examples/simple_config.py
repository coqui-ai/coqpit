

import os
from dataclasses import asdict, dataclass
from coqpit.coqpit import Coqpit, check_argument


@dataclass
class SimpleConfig(Coqpit):
    val_a: int = 10
    val_b: int = None
    val_d: float = 10.21
    val_c: str = "Coqpit is great!"

    def check_values(self,):
        '''Check config fields'''
        c = asdict(self)
        check_argument('val_a', c, restricted=True, min_val=10, max_val=2056)
        check_argument('val_b', c, restricted=True, min_val=128, max_val=4058, allow_none=True)
        check_argument('val_c', c, restricted=True)


if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))
    config = SimpleConfig()
    # print(config.serialize())
    # print(config.to_json())
    # config.save_json(os.path.join(file_path, 'example_config.json'))
    # config.load_json(os.path.join(file_path, 'example_config.json'))
    # print(config.pprint())

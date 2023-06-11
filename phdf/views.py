import pandas as pd
import numpy as np
from pathlib import Path
import random

APP_NAME = "phdf"
# local libraries
if __name__.startswith(APP_NAME):
    from . import utils
else:
    import utils


def read_hdf5_file(filepath: str):
    print(f"reading {filepath=}")
    store = pd.HDFStore(filepath)
    dflist = []
    for k in store.keys():
        df = store.get(k)
        print(f"{k=}: {df.shape=}")
        dflist.append(df)
    print("printing a random df:")
    df = random.choice(dflist)
    print(df)


def generate_pixel_array(
    n_row: int, n_col: int, use_str_col: bool = False
) -> pd.DataFrame:
    if use_str_col:
        df = pd.DataFrame(
            np.random.normal(0, 1, size=(n_row, n_col)),
            columns=[str(x) for x in range(n_col)],
        )
    else:
        df = pd.DataFrame(np.random.normal(0, 1, size=(n_row, n_col)))
    return df


def generate_sample_file(outname: str = "output.csv", mode: str = "csv"):
    filepath = Path(outname)
    mode = filepath.suffix
    match mode.lower():
        case ".csv":
            df = generate_pixel_array(40, 64)
            df.to_csv(filepath)
        case _:
            raise NotImplementedError(f"{mode=}")


if __name__ == "__main__":

    some_filepath = "nil-20230606_201824-cp3.h5"
    read_hdf5_file(utils.FileManager().get_resource_file(some_filepath)) # type: ignore

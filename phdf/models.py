import json
from dataclasses import dataclass
from typing import Mapping, NamedTuple, Optional
from pathlib import Path
import pandas as pd

from phdf import utils


@dataclass
class PixelData:
    site: str
    serialnumber: str
    coord: str
    ch: str
    value: float


class Table(NamedTuple):
    name: str
    df: pd.DataFrame


class DevicePixelArray:
    serialnumber: str
    tables: list[Table]
    h5_compression_level: int = 3
    outname: str = "nil"
    input_file: Path | None

    def __init__(self, inp: str | Path, output_folder: Optional[str] | Path = None):
        self.log = utils.setup_logger()
        self.tables = []

        self.df = pd.DataFrame()
        match inp:
            case str():
                file_content = self.process_json_strings(inp)
                file_content = self.decipher_json_strings(file_content)
                self.df = pd.DataFrame(file_content)  # finally, enter pandas
                self.outname = f"nil-{utils.get_time()}"
                self.input_file = None

            case Path():
                self.df = self.get_pixel_data_from_txt(inp)
                self.outname = inp.stem
                self.input_file = inp

            case _:
                raise NotImplementedError(f"{inp=}")

        self.outname = f"{self.outname}-cp{self.h5_compression_level}.h5"
        if output_folder is None:
            output_folder = utils.FileManager().go_up().cd("resources").get_cwd()
        else:
            output_folder = Path(output_folder)
        self.outpath = output_folder / self.outname

    def run(self):
        df = self.df
        df = self.process_raw_dataframe(df)
        for tn in df["table_name"].unique():
            self.add_df_array(tn, df)

    def get_pixel_data_from_txt(self, filepath: Path | str) -> pd.DataFrame:
        file_content = self.read_txt_file(filepath)  # gets a bunch of list[dict(json)]
        file_content = self.decipher_json_strings(file_content)  # tags the data
        df = pd.DataFrame(file_content)  # finally, enter pandas
        return df

    def read_txt_file(self, filepath: str | Path) -> list[Mapping]:
        """
        Digests the .txt file, which is a bunch of JSON strings,
        separated by commas

        :param filepath: file input
        :type filepath: str | Path
        :return: list of dictionary (from json strings)
        :rtype: list[Mapping]
        """
        with open(filepath, "r") as f:
            datastr = f.read()
        return self.process_json_strings(datastr)

    def process_json_strings(self, input_str: str) -> list[Mapping]:
        """Converts string into dict, using json.loads()

        :param input_str: _description_
        :type input_str: str
        :return: _description_
        :rtype: list[Mapping]
        """
        json_str_list = []
        for x in input_str.strip().split(","):
            try:
                if x:
                    d = json.loads(x)
                    json_str_list.append(d)
            except Exception as e:
                self.log.error(f"{e=}, {x=}")
        return json_str_list

    def decipher_json_strings(self, values: list[Mapping]) -> list[PixelData]:
        pixel_data_list = []
        for x in values:
            sn = list(x.keys())[0]
            x = x[sn]
            co = list(x.keys())[0]
            x = x[co]
            si = list(x.keys())[0]
            x = x[si]
            ch = list(x.keys())[0]
            ve = x[ch]
            pixel_data_list.append(
                PixelData(site=si, serialnumber=sn, coord=co, value=ve, ch=ch)
            )

        return pixel_data_list

    def process_raw_dataframe(self, dfin: pd.DataFrame) -> pd.DataFrame:
        """Adds name, col/row information to the dataframe

        :param dfin: _description_
        :type dfin: pd.DataFrame
        :return: _description_
        :rtype: pd.DataFrame
        """
        df = dfin
        df["table_name"] = df["site"] + "_" + df["serialnumber"] + "_" + df["ch"]
        df["row"] = df["coord"].apply(lambda x: int(x[1:3]))
        df["col"] = df["coord"].apply(lambda x: x[3:])
        df["value"] = pd.to_numeric(df["value"])
        return df

    def add_df_array(self, name: str, dfin: pd.DataFrame) -> None:
        """Shapes the data into pixel array and appends to tables: list[dataframe]

        :param name: _description_
        :type name: str
        :param dfin: _description_
        :type dfin: pd.DataFrame
        """
        df = dfin[dfin["table_name"] == name][["row", "col", "value"]]
        df = pd.pivot_table(df, columns="col", index="row", values="value")
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], downcast="float", errors="ignore")
        self.tables.append(Table(name=name, df=df))

    def save_to_hdf(self) -> Path:
        for i, table in enumerate(self.tables):
            if not self.outpath.parent.is_dir():
                self.outpath.parent.mkdir(parents=True, exist_ok=True)
            df = table.df
            df.to_hdf(
                self.outpath,
                key=table.name,
                mode="a",
                complevel=self.h5_compression_level,
            )
            self.log.info(f"{i}: appended({table.name}) to {self.outpath.name}")
        return self.outpath

    def cleanup(self):
        print("cleanup doing nothing")

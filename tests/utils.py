from pathlib import Path
import pandas as pd


class PathFinder:
    def __init__(self, resources_name: str = "resources"):
        self.cwd = Path(__file__).parent.parent

    def get_resources_path(self, name: str = "resources") -> Path:
        path = self.cwd / name
        if not path.is_dir():
            raise NotADirectoryError(f"{path=}")
        return path

    def get_image_files(
        self, file_ext: str = ".png", exclude_kw: str = ""
    ) -> list[Path]:
        resources_path = self.get_resources_path()
        if exclude_kw:
            imgs = [
                fp
                for fp in resources_path.rglob(f"*{file_ext}")
                if exclude_kw not in fp.stem
            ]
        else:
            imgs = [fp for fp in resources_path.rglob(f"*{file_ext}")]

        if not imgs:
            raise FileNotFoundError(f"no files found {file_ext=}")
        return imgs

    def generate_output_dir(self, name: str = "output") -> Path:
        output_dir = self.get_resources_path() / name
        if not output_dir.is_dir():
            output_dir.mkdir()
        return output_dir

    def get_filetable_images(self) -> pd.DataFrame:
        df = pd.DataFrame(pd.Series(self.get_image_files()), columns=["filepath"])
        df["foldername"] = df["filepath"].apply(lambda x: x.parent.name)
        return df


def main():
    _ = PathFinder()


if __name__ == "__main__":
    main()

import sys
import argparse
from phdf.main import launcher_json_string, launcher_fileio
from phdf import utils

APP_NAME = "phdf"
log = utils.setup_logger(APP_NAME)  # type: ignore


def main_fn():

    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Process given data into hdf5 container",
        epilog="""Example: python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/tmp/sample.hdf5'""",
        # /Users/jli8/Downloads
        # python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/Users/jli8/Downloads'
    )
    parser.add_argument(
        "data_input",
        help="Accepts 'filepath' |or| 'dataString', note that pure JSON (double quotes) might clash with some shells",
    )
    parser.add_argument(
        "output_dir",
        help="Output directory",
    )

    args = parser.parse_args()
    x = args.data_input

    if len(x) > 256:
        launcher_json_string(args.data_input, args.output_dir)
    elif (".txt" == x[-4:]) or (".TXT" == x[-4:]):
        launcher_fileio(args.data_input, args.output_dir)
    else:
        launcher_json_string(args.data_input, args.output_dir)

    return 0


if __name__ == "__main__":
    main_fn()

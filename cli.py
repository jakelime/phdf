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
        epilog="""Example: python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/tmp/sample.h5'""",
    )
    parser.add_argument(
        "data_input",
        help="Accepts 'filepath' |or| 'dataString' in JSON format",
    )
    parser.add_argument(
        "output_dir",
        help="Output directory",
    )
    parser.add_argument(
        "-scu",
        "--skip_cleanup",
        action="store_true",
        help="Skips clean up of the temporary.txt files",
    )

    args = parser.parse_args()

    if len(args.data_input) > 256:
        launcher_json_string(args.data_input, args.output_dir)

    elif (".txt" == args.data_input[-4:]) or (".TXT" == args.data_input[-4:]):
        launcher_fileio(
            args.data_input, args.output_dir, skip_cleanup=args.skip_cleanup
        )

    else:
        launcher_json_string(args.data_input, args.output_dir)

    return 0


if __name__ == "__main__":
    main_fn()

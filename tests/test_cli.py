import subprocess
from pathlib import Path
import pytest
import os
import platform
from utils import PathFinder

BASE_DIR = Path(__file__).parent.parent.resolve()


class PtConfigError(ValueError):
    """Exception raised when there are something wrong
    with configurations to run PyTest"""


def find_python() -> str:
    python_path = Path(".")
    current_os = platform.system()
    for py in ["python", "python3"]:
        match current_os:
            case "Darwin" | "Linux":
                p0 = subprocess.run(
                    [
                        "which",
                        py,
                    ],
                    capture_output=True,
                )
            case "Windows":
                p0 = subprocess.run(
                    [
                        "where.exe",
                        py,
                    ],
                    capture_output=True,
                )
            case _:
                raise NotImplementedError(f"{current_os=} is not supported")
        python_path = p0.stdout.decode("utf-8").split("\n")[0].strip()
        python_path = Path(python_path)
        if python_path.is_file():
            break
    if not python_path.is_file():
        raise PtConfigError("could not find python exe")

    return str(python_path.absolute())


def find_cli() -> str:
    cli_file = BASE_DIR / "cli.py"
    if not cli_file.is_file():
        raise PtConfigError("unable to find cli.py")
    return str(cli_file.absolute())


def generate_broken_commands():
    """
    Generates a list of commands that will raise an error
    (Test#1) phdf {MISSING ARGS}
    (Test#2) phdf {json string} {NO 2nd Arg}
    """
    return [
        ((find_python(), find_cli()), ("usage: ", "error: ")),
        (
            (
                find_python(),
                find_cli(),
                '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}',
            ),
            (
                "usage: ",
                "error: ",
            ),
        ),
    ]


def generate_commands():
    """
    Generates a list of commands that will work
    (Test#1) phdf {json string} {output dir}
    (Test#2) phdf {file IO} {output dir}
    """
    pytest_folder = BASE_DIR / "tests"
    resource_folder = BASE_DIR / "resources"
    rf_ = resource_folder.glob("*testfilewriter*.txt")
    input_file = next(rf_)

    return [
        (
            (
                find_python(),
                find_cli(),
                '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}',
                str(pytest_folder.absolute()),
            ),
            ("appended(", " to ", ".h5"),
        ),
        (
            (
                find_python(),
                find_cli(),
                str(input_file.absolute()),
                str(pytest_folder.absolute()),
            ),
            ("appended(", " to ", ".h5"),
        ),
    ]


def check_for_hdf5_output_files_and_cleanup():
    pytest_folder = BASE_DIR / "tests"
    output_files = [f for f in pytest_folder.glob("*.h5")]
    if output_files:
        for f in output_files:
            try:
                os.remove(f)
            except IOError as e:
                print(f"encountered {e=} while removing //{f.parent.name}/{f.name}")
    print("output files clean up completed")
    number_of_output_files = len(output_files)

    return number_of_output_files


@pytest.fixture(params=generate_broken_commands(), ids=["No args", "Missing args"])
def broken_commands_and_expected_kws(request):
    return request.param


@pytest.fixture(params=generate_commands(), ids=["using JSON string", "using FileIO"])
def commands_and_expected_kws(request):
    return request.param


def test_cli_incomplete_calls(broken_commands_and_expected_kws):
    """
    Test calls to the cli with no arguments, or broken commands
    Expect error messages to be returned
    """
    commands, keywords = broken_commands_and_expected_kws
    p0 = subprocess.run(
        commands,
        capture_output=True,
    )
    stderr = p0.stderr.decode("utf-8")
    kw_in_stderr = [(kw in stderr) for kw in keywords]
    assert all(kw_in_stderr)  # checks if expected keywords present


def test_cli(commands_and_expected_kws):
    """
    Test calls to the cli with working commands
    Expect hdf5 files in output dir and no errors
    """
    commands, keywords = commands_and_expected_kws
    p0 = subprocess.run(
        commands,
        capture_output=True,
    )
    stderr = p0.stderr.decode("utf-8")
    kw_in_stderr = [(kw in stderr) for kw in keywords]

    pathfinder = PathFinder()
    _ = pathfinder.generate_output_dir(name="pytest_generated_output")

    assert all(kw_in_stderr)  # checks if expected keywords present
    assert "ERROR   :" not in stderr  # checks that there are no errors logged
    assert check_for_hdf5_output_files_and_cleanup() > 0  # there must be output files


if __name__ == "__main__":

    """Simply type 'pytest' in the command line to execute the full test suite"""

    print(f"{find_python()=}")
    ## The functions below will be executed if this script is run
    ## using python test_cli.py
    #### IT IS NOT MEANT TO BE USED FOR ACTUAL CODE TEST ###
    # test_cli(generate_commands()[0])
    # for i in generate_broken_commands():
    #     test_cli_incomplete_calls(i)

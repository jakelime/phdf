import subprocess
from pathlib import Path
import pytest
import os
import platform

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
    cli_file = BASE_DIR / "push.py"
    if not cli_file.is_file():
        raise PtConfigError("unable to find cli.py")
    return str(cli_file.absolute())


def test_push_tc():
    """
    Test cli tool push.py using connection check
    """
    p0 = subprocess.run(
        [find_python(), find_cli(), "-tc"],
        capture_output=True,
    )
    stdout = p0.stdout.decode("utf-8")
    assert "ssh connection passed:" in stdout
    assert "Welcome to GitLab" in stdout



if __name__ == "__main__":

    """Simply type 'pytest' in the command line to execute the full test suite"""
    test_push_tc()

import subprocess
import enum
import os
import stat
import platform
import shutil
import argparse
from pathlib import Path
from typing import Any

from ppush import api

APP_NAME = "phdf"
EXPECTED_PYTHON_VERSION = "3.10"

class EnvVars(enum.Enum):
    REMOTE_SERVER = "REMOTE_SERVER"
    REMOTE_USER = "REMOTE_USER"
    REMOTE_PASSWORD = "REMOTE_PASSWORD"


class EnvironmentVarError(RuntimeError):
    """This exception is raised when a variable is not defined in the environment"""


class Manager:
    temp_dirname: str = ""
    git_payload_dir: Path | None
    payload_filepath: Path | None

    def __init__(
        self,
        git_manager: Any,
        temp_dirname: str = "Downloads",
    ):
        self.git_manager = git_manager
        self.temp_dirname = temp_dirname
        self.git_payload_dir = None
        self.payload_filepath = None

    @property
    def download_dir(self) -> Path:
        dir_download = Path(os.path.expanduser("~")) / self.temp_dirname
        if not dir_download.is_dir():
            raise NotADirectoryError(dir_download)
        return dir_download

    def run_git(self, skip_fetch: bool = False) -> Path:
        self.git_payload_dir = self.git_manager.run(
            target_dir=self.download_dir, skip_fetch=skip_fetch
        )
        return self.git_payload_dir

    def run_zip(self, exclude_git_folder=False) -> int:
        """run zip using shell on OSX/Linux, use python shutil to zip on win
        exclude_git_folder is ignored in win

        :param exclude_git_folder: excludes the .git folder (reduces size ),
        but loses access to git version control, defaults to False
        :type exclude_git_folder: bool, optional
        :raises RuntimeError: _description_
        :raises NotImplementedError: _description_
        :return: return code for the zip function
        :rtype: int
        """

        print("zipping...")
        if not self.git_payload_dir:
            raise RuntimeError("git_payload_dir is not init. please run_git() first")
        self.payload_filepath = (
            self.git_payload_dir.parent / f"payload-{APP_NAME}-{api.get_time()}.zip"
        )

        fnReturnCode = -1
        match (operating_system := platform.system()):
            case "Darwin" | "Linux":
                ## Commands are expected to be sent to bash

                if exclude_git_folder:
                    command = [
                        f"cd {self.git_payload_dir} ; zip -r {self.payload_filepath} . -x '.git/*'"
                    ]
                else:
                    command = [
                        f"cd {self.git_payload_dir} ; zip {self.payload_filepath} . -r"
                    ]
                _, _, fnReturnCode = handle_shell_command(command)

            case "Windows":
                ## cmd.exe shell does not have zip tool, use python shutil
                payload_filepath_ = f"{self.payload_filepath.absolute()}".split(".")[
                    0
                ]  # shutil has special requirements of no extensions
                shutil.make_archive(payload_filepath_, "zip", self.git_payload_dir)
                if self.payload_filepath.is_file():
                    fnReturnCode = 0

            case _:
                raise NotImplementedError(f"not yet available for {operating_system=}")

        return fnReturnCode

    def cleanup(self) -> None:
        print("cleaning up...")
        try:
            if self.git_payload_dir:
                shutil.rmtree(self.git_payload_dir, onerror=handle_readonly_error)
            print("cleanup complete")
        except OSError as e:
            print(f"{e=}")


class CliParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fn_storage = {}

    def add_argument_and_store_function(self, *args, **kwargs):
        """adds an argument using the .add_argument() method,
        and stores the arg mapping to function.
        """
        func = kwargs.pop("function")
        arg_name = args[1].strip("-")
        if not func:
            raise Exception("function kwarg must be provided")
        self.add_argument(*args, **kwargs)
        self.fn_storage[arg_name] = func


def handle_shell_command(command: list[str]) -> tuple[str, str, int]:
    """handles commands to the shell. returns a tuple of
    (stdout, stderr, returncode)
    """
    p0 = subprocess.run(command, capture_output=True, shell=True)
    stdout = p0.stdout.decode("utf-8")
    stderr = p0.stderr.decode("utf-8")
    return stdout, stderr, p0.returncode


def handle_readonly_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    ## Required for win in shutil.rmtree use cases
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

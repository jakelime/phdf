import subprocess
from pathlib import Path
from phdf import utils
import shutil
import os
import sys
from typing import Optional
import argparse
import dotenv
import paramiko
import socket
import platform
import enum

APP_NAME = "phdf"
BASE_DIR = Path(__file__).parent


class EnvVars(enum.Enum):
    REMOTE_SERVER = "REMOTE_SERVER"
    REMOTE_USER = "REMOTE_USER"
    REMOTE_PASSWORD = "REMOTE_PASSWORD"


class EnvironmentVarError(RuntimeError):
    """This exception is raised when a variable is not defined in the environment"""


class GitRepositoryNotUpdatedError(Exception):
    """raised when repository origin is not updated"""


class GitNotCleanError(Exception):
    """raised when there are changes not staged for commit"""


class GitManager:
    git_dir: Path
    payload_parent_dir: Optional[Path] = None
    payload_dir: Optional[Path] = None
    repo_url: str = ""

    def __init__(self, repo_url):
        self.git_dir = BASE_DIR
        self.repo_url = repo_url

    def run(self, target_dir: Path, branch: str = "", skip_fetch: bool = False) -> Path:
        """runs the default commands
        fetch, status, and clone
        """
        if not skip_fetch:
            self.fetch_status()
        payload_dir = self.clone(target_dir, branch)
        return payload_dir

    def fetch_status(self) -> int:
        print("getting git current status...")
        fnReturnCode = -1

        match (operating_system := platform.system()):
            case "Darwin" | "Linux":
                command = [f"cd {self.git_dir} ; git fetch ; git status"]
                stdout, _, fnReturnCode = self.handle_shell_command()
                p0 = subprocess.run(command, capture_output=True, shell=True)
                if ("Your branch is ahead" in stdout) and (
                    '(use "git push" to publish your local commits)' in stdout
                ):
                    raise GitRepositoryNotUpdatedError("please push your local commits")

                elif "Changes not staged for commit" in stdout:
                    raise GitNotCleanError("please check and commit changes first")

                elif ("Your branch is up to date" in stdout) and (
                    "nothing to commit, working tree clean" in stdout
                ):
                    print("git is clean.")
                else:
                    print(f"{p0=}")
                    raise GitNotCleanError("unexpected stdout. please check git status")

            case "Windows":
                command = [
                    "cd",
                    f"{str(self.git_dir.resolve())}",
                    "&&",
                    "git",
                    "fetch",
                    "&&",
                    "git",
                    "status",
                ]
                stdout, stderr, fnReturnCode = self.handle_shell_command(command)
                print(f"{stdout=}")
                print(f"{stderr=}")

                if "Changes not staged for commit" in stdout:
                    raise GitNotCleanError("please check and commit changes first")

                elif ("Your branch is ahead" in stdout) and (
                    'to publish your local commits' in stdout
                ):
                    raise GitRepositoryNotUpdatedError("please push your local commits")

                elif ("Your branch is up to date" in stdout) and (
                    "nothing to commit, working tree clean" in stdout
                ):
                    print("git is clean.")
                else:
                    print(f"{p0=}")
                    raise GitNotCleanError("unexpected stdout. please check git status")

            case _:
                raise NotImplementedError(f"not yet available for {operating_system=}")

        return fnReturnCode

    def clone(self, target_dir: Path, branch: str = "", blobless_clone=True) -> Path:
        print("cloning git from online repository...")
        print(f" >> {self.repo_url=}:{branch}")
        if target_dir.is_dir():
            self.payload_parent_dir = target_dir
            self.payload_dir = self.payload_parent_dir / "phdf"
        else:
            raise NotADirectoryError(f"invalid git clone {target_dir=}")

        if self.payload_dir.is_dir():
            try:
                backup_name = f"{self.payload_dir.stem}-backup{utils.get_time()}"
                old_git_dir = self.payload_dir.parent / backup_name
                os.rename(src=self.payload_dir, dst=old_git_dir)
            except OSError as e:
                print(f"is {self.payload_dir=} in use?")
                raise e

        git_clone_command = "git clone"
        if branch:
            git_clone_command = f"{git_clone_command} -b {branch}"

        if blobless_clone:
            git_clone_command = f"{git_clone_command} --filter=blob:none"

        command = [
            f"cd {self.payload_parent_dir} ; {git_clone_command} {self.repo_url}"
        ]
        p0 = subprocess.run(command, capture_output=True, shell=True)

        if not self.payload_dir.is_dir() or p0.returncode != 0:
            raise RuntimeError("failed to create payload dir")

        return self.payload_dir

    def handle_shell_command(self, command: list[str]) -> tuple[str, str, int]:
        """ handles commands to the shell. returns a tuple of
        (stdout, stderr, returncode)
        """
        p0 = subprocess.run(command, capture_output=True, shell=True)
        stdout = p0.stdout.decode("utf-8")
        stderr = p0.stderr.decode("utf-8")
        return stdout, stderr, p0.returncode


class LocalManager:
    base_dir: Optional[Path] = None
    git_payload_dir: Optional[Path] = None
    payload_filepath: Optional[Path] = None

    def __init__(self):
        self.base_dir = BASE_DIR
        self.git_manager = GitManager("git@gittf.ams-osram.info:os-opto-dev/phdf.git")

    @property
    def download_dir(self) -> Path:
        dir_download = Path(os.path.expanduser("~")) / "Downloads"
        if not dir_download.is_dir():
            raise NotADirectoryError(dir_download)
        return dir_download

    def run_git(self, skip_fetch: bool = False) -> Path:
        self.git_payload_dir = self.git_manager.run(
            target_dir=self.download_dir, skip_fetch=skip_fetch
        )
        return self.git_payload_dir

    def run_zip(self, exclude_git_folder=False) -> int:
        print("zipping...")
        if not self.git_payload_dir:
            raise RuntimeError("git_payload_dir is not init. please run_git() first")
        self.payload_filepath = (
            self.git_payload_dir.parent / f"payload-{APP_NAME}-{utils.get_time()}.zip"
        )
        if exclude_git_folder:
            command = [
                f"cd {self.git_payload_dir} ; zip -r {self.payload_filepath} . -x '.git/*'"
            ]
        else:
            command = [f"cd {self.git_payload_dir} ; zip {self.payload_filepath} . -r"]
        p0 = subprocess.run(command, shell=True)
        return p0.returncode

    def cleanup(self) -> None:
        print("cleaning up...")
        try:
            if self.git_payload_dir:
                shutil.rmtree(self.git_payload_dir)
        except OSError as e:
            print(f"{e=}")
        print("cleanup complete")


class RemoteManager:
    remote_server: Optional[str]
    user: Optional[str]
    _password: Optional[str]
    remote_payload_dir: str = ""
    remote_payload_filename: str = ""

    def __init__(self, remote_user: str = "", remote_server: str = ""):
        self.user = (
            os.environ.get(EnvVars.REMOTE_USER.value)
            if not remote_user
            else remote_user
        )
        if not self.user:
            raise EnvironmentVarError(
                f"{EnvVars.REMOTE_USER.value} not specified and not found in env vars"
            )

        self._password = os.environ.get(EnvVars.REMOTE_PASSWORD.value)
        if not self._password:
            raise EnvironmentVarError(
                f"{EnvVars.REMOTE_PASSWORD} not found in env vars"
            )

        self.remote_server = (
            os.environ.get("REMOTE_SERVER") if not remote_server else remote_server
        )
        if not self.remote_server:
            raise EnvironmentVarError(
                f"{EnvVars.REMOTE_SERVER} not specified not found in env vars"
            )

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def __str__(self):
        pwd = "###" if self._password else self._password
        return f"RemoteManager(url={self.user}@{self.remote_server}, {pwd=})"

    def connect(self):
        if not self.remote_server:
            raise ConnectionError(f"invalid remote_sever={self.remote_server}")
        try:
            self.ssh_client.connect(
                hostname=self.remote_server, username=self.user, password=self._password
            )
        except socket.gaierror as e:
            raise ConnectionError(f"{e}")

    def open_sftp(self, target_dirname="Downloads"):
        self.sftp_client = self.ssh_client.open_sftp()
        self.sftp_client.chdir(target_dirname)
        print(f"{self.sftp_client.getcwd()=}")
        self.remote_payload_dir = target_dirname

    def sftp_put(self, local_file: Path):
        print(f"uploading payload //{local_file.parent.name}/{local_file.name} ...")
        remote_f_obj = self.sftp_client.put(str(local_file.absolute()), local_file.name)
        print(f"{remote_f_obj.st_size=}")
        self.remote_payload_filename = local_file.name

    def mkdir(self, target_dirname: str = "Downloads", overwrite=False):
        """mkdir ``target_dirname`` on the remote server, relative to home (~)

        :param target_dirname: _description_, defaults to "Downloads"
        :type target_dirname: str, optional
        """
        command = f"[ -d '{target_dirname}' ] && echo 'true'"

        stdout, stderr = self.handle_ssh_command(command)
        results = stdout[0].strip().lower() if stdout else ""
        if results == "true":
            # exit because the target directory already exists
            return
        else:
            command = f"cd ~ ; mkdir '{target_dirname}'"
            print(f"making dir({target_dirname}) on remote server...")
            _ = self.handle_ssh_command(command)

    def handle_ssh_command(self, command: str) -> tuple[list[str], list[str]]:
        """send command to paramiko ssh_client
        gets stdout and stderr in list[str]

        :param command: a string of bash command, mulitple lines can be separated by ;
        :type command: str
        :return: (stdout, stderr)
        :rtype: tuple[list[str], list[str]]
        """
        _, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.readlines(), stderr.readlines()

    def print_command_outputs(self, stdout, stderr):
        stdout_parts = stdout.readlines()
        stderr_parts = stderr.readlines()
        print(f"{stdout_parts=}")
        print(f"{stderr_parts=}")

    def get_local_file(self, filepath_str: str = "~/Downloads/payload.zip") -> Path:
        if "~" in filepath_str:
            filepath = Path(os.path.expanduser(filepath_str))
        else:
            filepath = Path(filepath_str)
        if not filepath.is_file():
            raise FileNotFoundError(f"{filepath.absolute()=}")
        return filepath

    def run(self, payload_file: Path | str, remote_dirname: str = "Downloads") -> None:
        self.connect()
        self.mkdir(remote_dirname)
        self.remote_payload_dir = remote_dirname
        self.open_sftp(remote_dirname)
        match payload_file:
            case Path():
                if not payload_file.is_file():
                    raise FileNotFoundError(f"{payload_file.absolute()=}")
                payload = payload_file
            case str():
                payload = self.get_local_file(payload_file)
            case _:
                raise NotImplementedError
        self.remote_payload_filename = payload.name
        self.sftp_put(payload)
        self.run_remote_install(target_dir="python_repos")

    def check_conda(self):
        command = "conda --version"
        stdout, stderr = self.handle_ssh_command(command)
        if stdout:
            if "conda" in stdout[0]:
                print(
                    f"{stdout[0].strip()} installed on {self.user}@{self.remote_server}"
                )
                return True
        if stderr:
            if "conda: command not found" in stderr[0]:
                print(f"conda not found on {self.user}@{self.remote_server}")
                return False
        raise Exception(f"unexpected output from check_conda {stdout=}; {stderr=}")

    def run_remote_install(self, target_dir: str = "python_repos"):
        self.mkdir(target_dir)
        app_name = self.remote_payload_filename.split("-")[1]

        ## Checks if the app already exists in python_repos
        command = f"cd {target_dir} ; [ -d '{app_name}' ] && echo 'true'"
        stdout, stderr = self.handle_ssh_command(command)
        results = stdout[0].strip().lower() if stdout else ""
        if results == "true":
            print(f"remote {target_dir}/{app_name} already exist, removing ...")
            command = f"cd {target_dir} ; rm -rf {app_name}"
            _ = self.handle_ssh_command(command)
        self.mkdir(f"{target_dir}/{app_name}")
        command = f"cd ~ ; cd {self.remote_payload_dir} ; unzip {self.remote_payload_filename} -d ~/{target_dir}/{app_name}"
        stdout, stderr = self.handle_ssh_command(command)
        [print(x.strip()) for x in stdout]
        [print(x.strip()) for x in stderr]
        print("cleaning up ...")
        command = f"rm ~/{self.remote_payload_dir}/{self.remote_payload_filename}"
        stdout, stderr = self.handle_ssh_command(command)
        [print(x.strip()) for x in stdout]
        [print(x.strip()) for x in stderr]
        if not self.check_conda():
            print(f"WANRING: Anaconda (python3.10) is required to run {app_name}")
        print("install script end")


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


def run_push():
    lom = LocalManager()
    try:
        lom.run_git()
    except GitNotCleanError as ge:
        print(repr(ge))
        sys.exit(1)
    lom.run_zip()
    lom.cleanup()
    rmg = RemoteManager()
    rmg.run(payload_file=lom.payload_filepath)  # type: ignore


def run_push_specify_server(user_input: str):
    lom = LocalManager()
    try:
        lom.run_git()
    except GitNotCleanError as ge:
        print(repr(ge))
        sys.exit(1)
    lom.run_zip()
    lom.cleanup()
    if "@" in user_input:
        input_user, input_server = user_input.split("@")
        rmg = RemoteManager(remote_user=input_user, remote_server=input_server)
    else:
        rmg = RemoteManager(remote_server=user_input)
    rmg.run(payload_file=lom.payload_filepath)  # type: ignore


def run_push_simple():
    # exclude_git_folder
    pm = LocalManager()
    pm.run_git(skip_fetch=True)
    pm.run_zip(exclude_git_folder=True)
    pm.cleanup()
    sf = RemoteManager()
    try:
        sf.run(payload_file=pm.payload_filepath)  # type: ignore
    except ConnectionError as e:
        print(f"ERROR: {e=}")


def make_payload():
    """prepares the payload"""
    pm = LocalManager()
    pm.run_git()
    pm.run_zip()
    pm.cleanup()


def make_payload_simple():
    """makes the payload without ensure all changes are saved and commited"""
    pm = LocalManager()
    pm.run_git(skip_fetch=True)
    pm.run_zip()
    pm.cleanup()


def run_test_remote_connx():
    """test ssh connection to the remote"""
    try:
        sf = RemoteManager()
        sf.connect()
        print(f"ssh connection passed: {sf.remote_server}")
    except Exception as e:
        # raise e
        print(f"connx error. {e=}")


def new_dev_function():
    rm = RemoteManager()
    rm.connect()
    rm.remote_payload_dir = "Downloads"
    rm.remote_payload_filename = "payload-phdf-20230611_204231.zip"
    rm.run_remote_install()


def cli():
    parser = CliParser(
        prog="python push.py",
        description=f"Tool to push the {APP_NAME} into remote tester(s)",
        epilog="Usage example: python push.py -p",
    )
    parser.add_argument_and_store_function(
        "-p",
        "--push",
        action="store_true",
        help="Runs the full sequence of push and install commands",
        function=run_push,
    )
    parser.add_argument_and_store_function(
        "-ps",
        "--push_specify_server",
        action="store",
        help="Runs the full sequence of push, manually specify server URL",
        function=run_push,
    )
    parser.add_argument_and_store_function(
        "-pt",
        "--push_test",
        action="store_true",
        help="Runs a partial sequence of push and install (no fetch, exclude .git)",
        function=run_push_simple,
    )
    parser.add_argument_and_store_function(
        "-mp",
        "--make_payload",
        action="store_true",
        help="Run git pull, then zip to make the payload",
        function=make_payload,
    )
    parser.add_argument_and_store_function(
        "-tp",
        "--test_payload",
        action="store_true",
        help="Same as prepare_payload, but does not check git status. Used \
            for testing purposes",
        function=make_payload_simple,
    )
    parser.add_argument_and_store_function(
        "-tc",
        "--test_connection",
        action="store_true",
        help="Test SSH connection to the remote server",
        function=run_test_remote_connx,
    )
    parser.add_argument_and_store_function(
        "-d",
        "--dev",
        action="store_true",
        help="DEVELOPMENT ONLY. TEST NEW FUNCTIONS",
        function=new_dev_function,
    )

    args = parser.parse_args()

    counter = 0
    for kw, v in args._get_kwargs():
        if v:
            parser.fn_storage[kw]()  # executes the function
            counter += 1
            break  # only execute 1 function, even if there are multiple flags passed

    if counter == 0:
        parser.error("no args specified. use --help for more information")


def test_git_manager():
    gm = GitManager("git@gittf.ams-osram.info:os-opto-dev/phdf.git")
    print(f"{gm.git_dir=}")
    gm.fetch_status()


if __name__ == "__main__":
    dotenv.load_dotenv()
    # cli()
    test_git_manager()

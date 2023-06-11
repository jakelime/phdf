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

APP_NAME = "phdf"
BASE_DIR = Path(__file__).parent


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
        command = [f"cd {self.git_dir} ; git fetch ; git status"]
        p0 = subprocess.run(command, capture_output=True, shell=True)
        stdout = p0.stdout.decode("utf-8")
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
        return p0.returncode

    def clone(self, target_dir: Path, branch: str = "") -> Path:
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
        if branch:
            command = [
                f"cd {self.payload_parent_dir} ; git clone -b {branch} {self.repo_url}"
            ]
        else:
            command = [f"cd {self.payload_parent_dir} ; git clone {self.repo_url}"]
        p0 = subprocess.run(command, capture_output=True, shell=True)

        if not self.payload_dir.is_dir() or p0.returncode != 0:
            raise RuntimeError("failed to create payload dir")

        return self.payload_dir


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

    def __init__(self, remote_server: str = ""):
        self.user = os.environ.get("REMOTE_USER")
        self._password = os.environ.get("REMOTE_PASSWORD")
        self.remote_server = (
            os.environ.get("REMOTE_SERVER") if not remote_server else remote_server
        )

        if (not self.user) and (not self._password):
            raise EnvironmentVarError("user/password not found in env vars")

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
        except Exception as e:
            print(f"{e=}")



    def open_sftp(self, target_dirname="Downloads"):
        self.sftp_client = self.ssh_client.open_sftp()
        self.sftp_client.chdir(target_dirname)
        print(f"{self.sftp_client.getcwd()=}")

    def sftp_put(self, local_file: Path):
        print(f"uploading payload //{local_file.parent.name}/{local_file.name} ...")
        remote_f_obj = self.sftp_client.put(str(local_file.absolute()), local_file.name)
        print(f"{remote_f_obj.st_size=}")

    def ssh_remote_mkdir(self, target_dirname: str = "Downloads"):
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
        self.ssh_remote_mkdir(remote_dirname)
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
        self.sftp_put(payload)


def run_push():
    pm = LocalManager()
    try:
        pm.run_git()
    except GitNotCleanError as ge:
        print(repr(ge))
        sys.exit(1)
    pm.run_zip()
    pm.cleanup()
    sf = RemoteManager()
    sf.run(payload_file=pm.payload_filepath)  # type: ignore


def run_push_simple():
    # exclude_git_folder
    pm = LocalManager()
    pm.run_git(skip_fetch=True)
    pm.run_zip(exclude_git_folder=True)
    pm.cleanup()
    sf = RemoteManager()
    sf.run(payload_file=pm.payload_filepath)  # type: ignore


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


def test_remote_connection():
    """test ssh connection to the remote"""
    try:
        sf = RemoteManager()
        sf.connect()
        print(f"ssh connection passed: {sf.remote_server}")
    except Exception as e:
        print(f"connx error. {e=}")


def test_remote(user_input: str):
    """test ssh connection to the remote"""
    sf = RemoteManager()
    # sf.run(payload_file="~/Downloads/small_payload.zip")
    sf.run(payload_file=user_input)


def cli():
    parser = argparse.ArgumentParser(
        prog="python push.py",
        description=f"Tool to push the {APP_NAME} into remote tester(s)",
        epilog="Usage example: python push.py -p",
    )
    # parser.add_argument("method")
    parser.add_argument(
        "-p",
        "--push",
        action="store_true",
        help="Runs the full sequence of push commands",
    )
    parser.add_argument(
        "-pt",
        "--push_test",
        action="store_true",
        help="Runs the mini sequence of push commands (no fetch, small upload file)",
    )
    parser.add_argument(
        "-mp",
        "--make_payload",
        action="store_true",
        help="Run git pull, then zip to make the payload",
    )
    parser.add_argument(
        "-tp",
        "--test_payload",
        action="store_true",
        help="Same as prepare_payload, but does not check git status. Used \
            for testing purposes",
    )
    parser.add_argument(
        "-tc",
        "--test_connection",
        action="store_true",
        help="Test SSH connection to the remote server",
    )
    parser.add_argument(
        "-tu",
        "--test_upload",
        action="store",
        help="Test uploading file to remote server",
    )
    args = parser.parse_args()

    if args.push:
        run_push()
    elif args.push_test:
        run_push_simple()
    elif args.test_connection:
        test_remote_connection()
    elif args.make_payload:
        make_payload()
    elif args.test_payload:
        make_payload_simple()
    else:
        parser.error("no args specified. use --help for more information")


if __name__ == "__main__":
    dotenv.load_dotenv()
    cli()

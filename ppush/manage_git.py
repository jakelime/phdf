import platform
from pathlib import Path
import os

from ppush import api
from ppush.core import handle_shell_command


class GitNotCleanError(Exception):
    """raised when there are changes not staged for commit"""


class GitRepositoryNotUpdatedError(Exception):
    """raised when repository origin is not updated"""


class GitManager:
    git_base_dir: Path | str = ""
    payload_parent_dir: Path | str = ""
    payload_dir: Path | str = ""
    repo_url: str = ""

    def __init__(self, git_base_dir: Path | str, repo_url: str):
        if not git_base_dir:
            raise RuntimeError("git_base_dir not specified")
        self.git_base_dir = git_base_dir
        if not repo_url:
            raise RuntimeError("repo_url not specified")
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
                ## Commands are expected to be sent to bash
                command = [f"cd {self.git_base_dir} ; git fetch ; git status"]

            case "Windows":
                ## Commands are expected to be sent to cmd.exe shell for Windows case
                if isinstance(self.git_base_dir, Path):
                    command = [
                        "cd",
                        f"{str(self.git_base_dir.resolve())}",
                        "&&",
                        "git",
                        "fetch",
                        "&&",
                        "git",
                        "status",
                    ]
                else:
                    raise RuntimeError(f"unxpected {self.git_base_dir=}")

            case _:
                raise NotImplementedError(f"not yet available for {operating_system=}")

        stdout, stderr, fnReturnCode = handle_shell_command(command)
        self.check_git_output(stdout, stderr)
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
                backup_name = f"{self.payload_dir.stem}-backup{api.get_time()}"
                old_git_dir = self.payload_dir.parent / backup_name
                os.rename(src=self.payload_dir, dst=old_git_dir)
            except OSError as e:
                print(f"is {self.payload_dir=} in use?")
                raise e

        match (operating_system := platform.system()):
            case "Darwin" | "Linux":
                ## Commands are expected to be sent to bash
                git_clone_command = "git clone"
                if branch:
                    git_clone_command = f"{git_clone_command} -b {branch}"

                if blobless_clone:
                    git_clone_command = f"{git_clone_command} --filter=blob:none"

                command = [
                    f"cd {self.payload_parent_dir} ; {git_clone_command} {self.repo_url}"
                ]

            case "Windows":
                ## Commands are expected to be sent to cmd.exe shell for Windows case
                git_clone_command = ["git", "clone"]
                if branch:
                    git_clone_command.append("-b")
                    git_clone_command.append(branch)
                if blobless_clone:
                    git_clone_command.append("--filter=blob:none")
                git_clone_command.append(self.repo_url)

                command = [
                    "cd",
                    str(self.payload_parent_dir.absolute()),
                    "&&",
                ]
                for c in git_clone_command:
                    command.append(c)

            case _:
                raise NotImplementedError(f"not yet available for {operating_system=}")

        stdout, stderr, returncode = handle_shell_command(command)

        if not self.payload_dir.is_dir() or returncode != 0:
            print(f"command={' '.join(command)}")
            print(f"{stdout=}")
            print(f"{stderr=}")
            raise RuntimeError("failed to create payload dir")

        return self.payload_dir

    def check_git_output(self, stdout: str, stderr: str):
        if "Changes not staged for commit" in stdout:
            raise GitNotCleanError("please check and commit changes first")

        elif ("Your branch is ahead" in stdout) and (
            "to publish your local commits" in stdout
        ):
            raise GitRepositoryNotUpdatedError("please push your local commits")

        elif ("Your branch is up to date" in stdout) and (
            "nothing to commit, working tree clean" in stdout
        ):
            print("git is clean.")
        else:
            print(f"{stdout=}")
            print(f"{stderr=}")
            raise GitNotCleanError("unexpected stdout. please check git status")

    @staticmethod
    def run_ssh_test_command():
        print("testing SSH connection to gittf...")
        match (operating_system := platform.system()):
            case "Darwin" | "Linux":
                ## Commands are expected to be sent to bash
                command = ["ssh -T git@gittf.ams-osram.info"]

            case "Windows":
                ## Commands are expected to be sent to cmd.exe shell for Windows case
                command = [
                    "ssh",
                    "-T",
                    "git@gittf.ams-osram.info",
                ]

            case _:
                raise NotImplementedError(f"not yet available for {operating_system=}")
        stdout, stderr, _ = handle_shell_command(command)
        [print(line) for line in stdout.splitlines()]
        [print(line) for line in stderr.splitlines()]

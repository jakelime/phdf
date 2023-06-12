import os
import paramiko
import socket

from pathlib import Path
from typing import Optional

from ppush.core import EnvVars, EnvironmentVarError
from ppush.core import EXPECTED_PYTHON_VERSION

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

    def run(self, payload_file: Path | str | None, remote_dirname: str = "Downloads") -> None:
        self.connect()
        self.mkdir(remote_dirname)
        self.remote_payload_dir = remote_dirname
        self.open_sftp(remote_dirname)
        if not payload_file:
            raise RuntimeError("no payload file specified")
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
            print(f"WANRING: Anaconda (python{EXPECTED_PYTHON_VERSION}) is required to run {app_name}")
        print("install script end")
        print(
            "Usage: \n  conda activate\n  python {phdf-path/cli.py} {jsonString} {outpath.h5}\n  python {phdf-path/cli.py} {jsonFile.txt} {outpath.h5}"
        )

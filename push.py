import sys
import dotenv
import os
from pathlib import Path

from ppush.manage_git import GitManager
from ppush.manage_git import GitNotCleanError
from ppush.manage_remote import RemoteManager
from ppush.core import PushManager, CliParser, Manager, EnvVars

from phdf.main import APP_NAME

BASE_DIR = Path(__file__).parent
REPO_URL = "git@gittf.ams-osram.info:os-opto-dev/phdf.git"
TEMP_DIRNAME = "Downloads"


class PhdfPushManager(metaclass=PushManager):
    def __init__(self):
        self.repo_url = REPO_URL
        self.git_base_dir = BASE_DIR / "phdf"

    def push(self):
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
        try:
            mgr.run_git()
        except GitNotCleanError as ge:
            print(repr(ge))
            sys.exit(1)
        mgr.run_zip()
        mgr.cleanup()
        rmg = RemoteManager()
        rmg.run(payload_file=mgr.payload_filepath)  # type: ignore

    def push_specify_server(self, user_input: str):
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
        try:
            mgr.run_git()
        except GitNotCleanError as ge:
            print(repr(ge))
            sys.exit(1)
        mgr.run_zip()
        mgr.cleanup()
        if "@" in user_input:
            input_user, input_server = user_input.split("@")
            rmg = RemoteManager(remote_user=input_user, remote_server=input_server)
        else:
            rmg = RemoteManager(remote_server=user_input)
        rmg.run(payload_file=mgr.payload_filepath)

        gm = GitManager(
            git_base_dir=self.git_base_dir,
            repo_url=self.repo_url,
        )
        gm.run_ssh_test_command()

    def push_test(self):
        # exclude_git_folder
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
        mgr.run_git(skip_fetch=True)
        mgr.run_zip()
        mgr.cleanup()
        rmg = RemoteManager()
        try:
            rmg.run(payload_file=mgr.payload_filepath)
        except ConnectionError as e:
            print(f"ERROR: {e=}")

    def make_payload(self):
        """prepares the payload"""
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
        mgr.run_git()
        mgr.run_zip()
        mgr.cleanup()

    def make_payload_simple(self):
        """makes the payload without ensure all changes are saved and commited"""
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
        mgr.run_git(skip_fetch=True)
        mgr.run_zip()
        mgr.cleanup()


def run_test_remote_connx():
    """test ssh connection to the remotes"""
    try:
        print("============ CONNECTION TESTS ============")
        print("  -- initiating connection to gittf.ams-osram.info --")
        gm = GitManager(
            git_base_dir=BASE_DIR,
            repo_url=REPO_URL,
        )
        gm.run_ssh_test_command()

        print("\n  -- initiating connection to remote tester(s) --")
        remote_servers = os.environ.get(EnvVars.REMOTE_SERVER_LIST.value)
        if remote_servers:
            remote_servers = remote_servers.split(",")
            n = len(remote_servers)
            for i, server in enumerate(remote_servers, 1):
                try:
                    server = server.strip()
                    print(
                        f"[{i}/{n}] testing connection to remote server ({server})..."
                    )
                    rmg = RemoteManager(remote_server=server)
                    rmg.connect()
                    print(" >> ssh connection successful")
                except Exception as e:
                    print(e)
                    continue
        else:
            server = os.environ.get(EnvVars.REMOTE_SERVER.value)
            print(f"testing connection to single remote server({server}) ...")
            rmg = RemoteManager()
            rmg.connect()
            print(" >> ssh connection successful")
            print(
                f"(you can specify a list of servers in \
{EnvVars.REMOTE_SERVER_LIST.value} to test multiple servers)"
            )
        print("========== END OF CONNECTION TESTS ==========")

    except Exception as e:
        print(f"connx error. {e=}")


def new_dev_function():
    print("Nothing to do")


def cli():
    phdf_pm = PhdfPushManager()
    parser = CliParser(
        prog="python push.py",
        description=f"Tool to push the {APP_NAME.upper()} into remote tester(s)",
        epilog="Usage example: python push.py -p",
    )

    parser.add_argument_and_store_function(
        "-tc",
        "--test_connection",
        action="store_true",
        help="Test SSH connection to the remote server(s), and gittf",
        function=run_test_remote_connx,
    )

    parser.add_argument_and_store_function(
        "-p",
        "--push",
        action="store_true",
        help="Runs the full sequence of push and install commands",
        function=phdf_pm.push,
    )
    parser.add_argument_and_store_function(
        "-ppt",
        "--push_test",
        action="store_true",
        help="Runs push, but skips git status checks",
        function=phdf_pm.push,
    )
    parser.add_argument_and_store_function(
        "-pps",
        "--phdf_push_specify_server",
        action="store",
        help="Runs push, with specified server url",
        function=phdf_pm.push_specify_server,
    )
    parser.add_argument_and_store_function(
        "-pmp",
        "--phdf_make_payload",
        action="store_true",
        help="Run git pull, then zip to make the payload",
        function=phdf_pm.make_payload,
    )
    parser.add_argument_and_store_function(
        "-ptp",
        "--phdf_test_payload",
        action="store_true",
        help="phdf: Same as prepare_payload, but does not check git status. Used \
for testing purposes",
        function=phdf_pm.make_payload_simple,
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
            if isinstance(v, bool):
                parser.fn_storage[kw]()  # executes the function
                counter += 1
            elif isinstance(v, str):
                parser.fn_storage[kw](v)  # executes the function with arg
                counter += 1
            break  # only execute 1 function, even if there are multiple flags passed

    if counter == 0:
        parser.error("no args specified. use --help for more information")


if __name__ == "__main__":
    dotenv.load_dotenv()
    cli()

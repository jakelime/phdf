import sys
import dotenv
import os
from pathlib import Path

from ppush.manage_git import GitManager
from ppush.manage_git import GitNotCleanError
from ppush.manage_remote import RemoteInstallManager
from ppush.core import LocalManager, CliParser
from ppush.core import PushManager, EnvVars

from phdf.main import APP_NAME

BASE_DIR = Path(__file__).parent
REPO_URL = "git@gittf.ams-osram.info:os-opto-dev/phdf.git"
LOCAL_TEMP_DIRNAME = "Downloads"
REMOTE_TEMP_DIRNAME = "Downloads"


class PhdfPushManager(metaclass=PushManager):
    def __init__(self):
        self.repo_url = REPO_URL
        self.git_base_dir = BASE_DIR / "phdf"

    def push(self, skip_fetch: bool = False):
        gmr = GitManager(
            repo_url=self.repo_url,
            git_base_dir=self.git_base_dir,
            skip_fetch=skip_fetch,
        )
        lmg = LocalManager(git_mgr=gmr, target_tmp_dir=LOCAL_TEMP_DIRNAME)
        rim = RemoteInstallManager()

        try:
            lmg.run()
        except GitNotCleanError as ge:
            print(repr(ge))
            sys.exit(1)
        rim.run(
            payload_file=lmg.payload_filepath,
            remote_target_dirname=REMOTE_TEMP_DIRNAME,
            install_to="python_repos",
        )

    def push_specify_server(self, user_input: str):
        gmr = GitManager(repo_url=self.repo_url, git_base_dir=self.git_base_dir)
        lmg = LocalManager(git_mgr=gmr, target_tmp_dir=LOCAL_TEMP_DIRNAME)
        if "@" in user_input:
            input_user, input_server = user_input.split("@")
            rim = RemoteInstallManager(
                remote_user=input_user, remote_server=input_server
            )
        else:
            rim = RemoteInstallManager(remote_server=user_input)

        try:
            lmg.run()
        except GitNotCleanError as ge:
            print(repr(ge))
            sys.exit(1)

        rim.run(
            payload_file=lmg.payload_filepath,
            remote_target_dirname=REMOTE_TEMP_DIRNAME,
            install_to="python_repos",
        )

    def push_test(self):
        # skips checking if there are uncommitted changes
        self.push(skip_fetch=True)

    def make_payload(self, skip_fetch: bool = False):
        """makes the payload file"""
        gmr = GitManager(
            repo_url=self.repo_url,
            git_base_dir=self.git_base_dir,
            skip_fetch=skip_fetch,
        )
        lmg = LocalManager(git_mgr=gmr, target_tmp_dir=LOCAL_TEMP_DIRNAME)
        lmg.run()

    def make_payload_simple(self):
        """makes the payload without ensure all changes are saved and commited"""
        self.make_payload(skip_fetch=True)


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
                    rmg = RemoteInstallManager(remote_server=server)
                    rmg.open_ssh()
                    print(" >> ssh connection successful")
                except Exception as e:
                    print(e)
                    continue
        else:
            server = os.environ.get(EnvVars.REMOTE_SERVER.value)
            print(f"testing connection to single remote server({server}) ...")
            rmg = RemoteInstallManager()
            rmg.open_ssh()
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
        "-pt",
        "--push_test",
        action="store_true",
        help="Runs push, but skips git status checks. For testing purposes",
        function=phdf_pm.push_test,
    )
    parser.add_argument_and_store_function(
        "-ps",
        "--push_specify_server",
        action="store",
        help="Runs push, with specified server url",
        function=phdf_pm.push_specify_server,
    )
    parser.add_argument_and_store_function(
        "-pl",
        "--make_payload",
        action="store_true",
        help="Run git pull, then zip to make the payload",
        function=phdf_pm.make_payload,
    )
    parser.add_argument_and_store_function(
        "-plt",
        "--make_payload_test",
        action="store_true",
        help="Same as prepare_payload, but does not check git status. \
For testing purposes",
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

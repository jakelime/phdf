import sys
import dotenv
from pathlib import Path

from ppush.manage_git import GitManager
from ppush.manage_git import GitNotCleanError
from ppush.manage_remote import RemoteManager
from ppush.core import CliParser, Manager
from ppush.core import APP_NAME

REPO_URL = "git@gittf.ams-osram.info:os-opto-dev/phdf.git"
BASE_DIR = Path(__file__).parent
TEMP_DIRNAME = "Downloads"


def run_push():
    gmr = GitManager(repo_url=REPO_URL, git_base_dir=BASE_DIR)
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


def run_push_specify_server(user_input: str):
    gmr = GitManager(repo_url=REPO_URL, git_base_dir=BASE_DIR)
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


def run_push_simple():
    # exclude_git_folder
    gmr = GitManager(repo_url=REPO_URL, git_base_dir=BASE_DIR)
    mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
    mgr.run_git(skip_fetch=True)
    mgr.run_zip(exclude_git_folder=True)
    mgr.cleanup()
    rmg = RemoteManager()
    try:
        rmg.run(payload_file=mgr.payload_filepath)
    except ConnectionError as e:
        print(f"ERROR: {e=}")


def run_test_remote_connx():
    """test ssh connection to the remote"""
    try:
        print("testing connection to remote server...")
        rmg = RemoteManager()
        rmg.connect()
        print(f" >> ssh connection passed: {rmg.remote_server}")
    except Exception as e:
        print(f"connx error. {e=}")

    gm = GitManager(
        git_base_dir=BASE_DIR,
        repo_url=REPO_URL,
    )
    gm.run_ssh_test_command()


def make_payload():
    """prepares the payload"""
    gmr = GitManager(repo_url=REPO_URL, git_base_dir=BASE_DIR)
    mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
    mgr.run_git()
    mgr.run_zip()
    mgr.cleanup()


def make_payload_simple():
    """makes the payload without ensure all changes are saved and commited"""
    gmr = GitManager(repo_url=REPO_URL, git_base_dir=BASE_DIR)
    mgr = Manager(git_manager=gmr, temp_dirname=TEMP_DIRNAME)
    mgr.run_git(skip_fetch=True)
    mgr.run_zip()
    mgr.cleanup()


def new_dev_function():
    print("Nothing to do")


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
        function=run_push_specify_server,
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
        help="Test SSH connection to the remote server, and gittf",
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

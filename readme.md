# PHDF: Python HDF5 solution for interfacing with Smartest8

## Notice

v1.0.0+ has major code changes, implemented a solution with well
structured OOP and also used real examples from the actual test program
IO.

## TODO:

### Usage

#### From `python`

``` bash
# Use a JSON string
python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/Users/jli8/Downloads'

# Use a file.txt, containing a list of the JSON strings separated by commas
python cli.py /Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt /Users/jli8/Downloads
python python cli.py ~/python_repos/phdf/resources/testfilewriter-2047225563688979.txt ~/Documents
```

The `cli` needs 2 arguments

**data_input**

:   accept a filepath, or `JSON` string in a specific format.

**output_dir**

:   accept a file directory. Exception will be raised if dir does not
    exist.

*JSON String format*

:   Must be a string that in this format:
    `{"partId": {"R00C00": {"site1":{"aTB_0": "0.0"}}}}`.

Do take care of the double quotes `"` and single quotes `'`.

-   `Java` specifies that `String` must be enclosed with `"`
-   `JSON` specifies that `key` and `values` must be enclosed with `"`
-   In `python`, `"` or `'` can be interchanged with flexibility
-   In `bash`, `'` means literal strings, we can use it to encase like
    this `'{"a": "1"}'`

#### Interfacing to Java using subprocess to call python

We will use Java\'s
`ProcessBuilder builder = new ProcessBuilder(command);`,

A simple example of how to implement:

-   `Main.java` is the entry point to call `Phdf.java`
-   `Phdf` java class is basically a process builder/manager to a call a
    new process
-   We use the `Phdf` class to intiate a subprocess call to
    `python cli commands`

A simple execution example:

``` java
public static void main(String[] args) {
    // Initialize
    Phdf processor = new Phdf();
    // Run the CLI tool
    processor.run("{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}", "/Users/jli8/Downloads");
}
```

Output:

``` bash
(p311) ➜  200-phdf git:(wip) ✗ javac Main.java
(p311) ➜  200-phdf git:(wip) ✗ java Main
PhdfProcess initialized
command iniialized: [/Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py]
>> calling subprocess phdf (data.length=52) /Users/jli8/Downloads
INFO    : 0: appended(site1_partId1_aTB_0) to  self.outpath.name='nil-20230607_090809-cp3.h5'
>> phdf completed with exitCode=0
```

### Installation

Some of the DevOps features are available in this repo.

#### To distribute to remote testers

**Requirements:**

-   Local machine (`OSX` / `Win`) with connection to both
    `Remote Tester` and `gittf`
-   Remote tester: `rbgv93k0001.int.osram-light.com`

**On your the local machine**

1.  Set up your SSH connection to the `gitf repo` if you haven\'t
    already done so. SSH setup guide is available in Github/Gitlab docs
    and also some of my other project\'s readme.

2.  Test your connection to `remote tester` and `gittf` using
    `python push.py -tc`

    ``` bash
    (p311) ➜  200-phdf git:(debugPs) ✗ python push.py -tc
    testing connection to remote server...
    >> ssh connection passed: rbgv93k0001.int.osram-light.com
    testing SSH connection to gittf...
    Welcome to GitLab, @jake.lim!
    ```

3.  Run the push command: `python push.py --push`

    > ``` bash
    > (p311) ➜  200-phdf git:(debugPs) python push.py -p
    > cloning git from online repository...
    > >> self.repo_url='git@gittf.ams-osram.info:os-opto-dev/phdf.git':
    > zipping...
    > cleaning up...
    > self.sftp_client.getcwd()='/home/j.lim2/Downloads'
    > uploading payload //Downloads/payload-phdf-20230612_145919.zip ...
    > making dir(python_repos/phdf) on remote server...
    > Archive:  payload-phdf-20230612_145919.zip
    > ...
    > cleaning up ...
    > conda 23.3.1 installed on j.lim2@rbgv93k0001.int.osram-light.com
    > install script end
    > Usage:
    > conda activate
    >     python {phdf-path/cli.py} {jsonString} {outpath.h5}
    >     python {phdf-path/cli.py} {jsonFile.txt} {outpath.h5}
    > ```

**On the remote tester**

1.  If Anaconda has not been installed, please download and install
    latest Anaconda for Linux
    [distribution](https://www.anaconda.com/download#downloads)

2.  Either connect by using `SSH` into the remote tester, or `VNC` to
    use the terminal `shell` .

3.  The `phdf` application is installed in `~/python_repos/phdf`

    The `python` path for Anaconda (default) is installed in
    `~/anaconda3/bin/python`

    Test the app by running the command in your shell:

    `python cli.py {jsonString} {outputPath}`

    ``` bash
    [j.lim2@rbgv93k0001 ~]$ ~/anaconda3/bin/python ~/python_repos/phdf/cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' ~/Documents
    INFO    : 0: appended(site1_partId_aTB_0) to  self.outpath.name='nil-20230612_151141-cp3.h5'
    ```

4.  Or, if you are familiar with using `conda`, do it the proper way

    ``` bash
    [j.lim2@rbgv93k0001 phdf]$ conda activate
    (base) [j.lim2@rbgv93k0001 phdf]$ python cli.py ~/python_repos/phdf/resources/testfilewriter-2047225563688979.txt ~/Documents
    INFO    : 0: appended(site1_partId1_aTB_0) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
    ...
    INFO    : 18: appended(site2_partId1_aTB_8) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
    INFO    : 19: appended(site2_partId1_aTB_9) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
    ```

### Running `pytest`

There is a full code testing suite in the `tests` dir .Run `pytest` from
your cli to ensure that the code is working properly

``` bash
cd tests
pytest # You can run simply without any flag, then you will only see warnings and errors
pytest -v # -v is a verbose flag, to show you which are tests running
```

Example results from a full test suite

``` bash
(p311) ➜  tests git:(main) pytest -v
============================================== test session starts ===============================================
platform darwin -- Python 3.11.3, pytest-7.2.2, pluggy-1.0.0 -- /Users/jli8/miniconda3/envs/p311/bin/python3.11
cachedir: .pytest_cache
rootdir: /Users/jli8/activedir/200-phdf/tests
plugins: typeguard-2.13.3, cov-4.0.0, anyio-3.6.2, dash-2.9.1
collected 4 items

test_cli.py::test_cli_incomplete_calls[No args] PASSED                                                     [ 25%]
test_cli.py::test_cli_incomplete_calls[Missing args] PASSED                                                [ 50%]
test_cli.py::test_cli[using JSON string] PASSED                                                            [ 75%]
test_cli.py::test_cli[using FileIO] PASSED                                                                 [100%]

=============================================== 4 passed in 6.30s ================================================
```

You can get pytest using `pip install pytest` on your own environment or
simply use the DevOps installation script to install the full
environment (bare minimum + push + test).

### Notes

Unfortunately, we will face problems if we try to pass the entire
`JSON string` into the command. The length of the string is too long
(`length=1356801`), which gives us `error=7, Argument list too long`.

One alternative is to write the data using `FileIO`, then pass the
filepath to the command.

``` java
import eviyos2g.lib.shared.common.util.CustomFileWriter;
public static void main(String[] args) {
    // Write data to FileIO
    String jsonFilepath = "/home/j.lim2/tmp/testfilewriter-" + System.nanoTime() + ".txt";
    String jsonString = "{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}"
    CustomFileWriter fileWriter = new CustomFileWriter(test_outname);
    fileWriter.write(jsonString);

    // Run the CLI tool
    Phdf processor = new Phdf();
    processor.run(jsonFilepath, "/home/j.lim2/tmp/");
}
```

Output:

``` bash
(p311) ➜  200-phdf git:(wip) ✗ javac Main.java
(p311) ➜  200-phdf git:(wip) ✗ java Main
intiailised filepath = /Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt
jsonString length is 1356801
command iniialized: [/Users/jli8/anaconda3/bin/python, /Users/jli8/gitRepos/phdf/cli.py]
PhdfProcess initialized
command iniialized: [/Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py]
>> calling subprocess phdf (data.length=76) /Users/jli8/Downloads
INFO    : 0: appended(site1_partId1_aTB_0) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
INFO    : 1: appended(site1_partId1_aTB_1) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
...
INFO    : 18: appended(site2_partId1_aTB_8) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
INFO    : 19: appended(site2_partId1_aTB_9) to  self.outpath.name='testfilewriter-2047225563688979-cp3.h5'
>> phdf completed with exitCode=0
```

### Changelogs

-   v1.0.5
    -   added push.py for DevOps
-   v1.0.3
    -   added pytest, with a total of 4 critical basic tests
        -   2 tests to CLI for invalid arguments given
        -   test to CLI using JSON string
        -   test to CLI using File as input
-   v1.0.2
    -   updated readme
    -   updated java codes and entry points
-   v1.0.0 / v1.0.1
    -   Properly structured into `models.py`, `views.py` and `main.py`
        (presenter)
    -   Entry point will be `cli.py` where it calls \"launcher\" from
        `presenter`
    -   `cli.py` reworked with `argparse` for fully supported CLI with
        help and instructions
    -   `tests.py` structured to be used for code testing
    -   `views.py` primary function is to interact the data, view
        dataframe and plot pixelMaps
    -   `models.py` defines the working model, data structures of our
        device
-   v0.0.2
    -   Packaged java class `Phdf` into a separate package
    -   `Main.java` will be an entry point to instantiate `process`
        object, then call `process.run()` method to execute
-   v0.0.3
    -   Worked out some kinks during debugging when integrating into
        SMT8
    -   `Phdf.java`: some hard-coded variables are now changed to match
        environment of `rbgv93k0001.int.osram-light.com`
-   v0.0.1
    -   first draft version released

### Environment Setup and Installation

This section describes how to set up a basic environment to use python.

Note that this part may be already been outdated, we can use automated
scripting tools to install the entire test program here in
[smt8-hdf](https://gittf.ams-osram.info/os-opto-dev/smt8-hdf), which is
another repo with the full test program with the interface already
programmed into the SMT test program.

#### Setting up Python environment

1.  We use standard python packaging techniques here. A simple example
    for bare minimal install manually:

    ``` bash
    ## Using python==3.10
    python3 -m venv venv
    source ./venv/bin/activate
    which python
    pip install tables
    pip install pandas
    pip install pyinstaller
    ```

2.  Another one of the standard methods to install from pip
    requirements.txt:

    ``` bash
    ## Full libraries consist of packages for
    # - Bare minimum depedencies
    # - DevOps (PUSH TO SERVER)
    # - PyTest for code testing
    pip install -r requirements-osx-full.txt

    ## Bare minimum dependencies to execute in production
    pip install -r requirements-osx-minimum.txt

    ## How to make req.txt from your current env
    pip freeze > requirements.txt
    ```

3.  Use `Bash` script for automated `venv` execution. This method will
    pull the latest versions of depedencies from PyPI. It should work
    most of the time, but not guaranteed.

    ``` bash
    ## To install bare minimum dependencies for production
    bash make_venv.sh

    ## To install full suite, including PyTest and DevOps (SSH integration)
    base make_venv.sh full
    ```

4.  To view the dependencies, read the function
    `install_python_libraries_full` from `make_venv.sh`.

    This codebase employs the use of new python syntax such walrus
    operator and type hinting.

    Recommended `python>=3.10` because of the `match statements` and
    `type hinting` used.

    Recommended test environment `python3.10` because Anaconda\'s latest
    Linux distribution as of today is still `python3.10`. Using
    `python3.11` will work most of the time, but there are notable new
    in type hintings not compatible to `python3.10`.

    Refactoring for compatibility with `python3.8` for compatibility to
    `win7` is possible. Remove the type hints and replace `match`
    statements with `if else` statements.

#### Setting up Bash on Windows using WSL

1.  Download the Windows Subsystem for Linux, developed by Microsoft
    from the [Microsoft
    Store](https://www.microsoft.com/store/productId/9P9TQF7MRM4R)

2.  Activate your shell by typing `bash` in cmd / pwsh

    Remember update your shell as standard practices

    ``` bash
    sudo apt-get update
    sudo apt-get upgrade
    ```

    Get the usual tools we need (it might not be pre-installed,
    depending on which WSL you chose)

    ``` bash
    sudo apt-get install zip
    sudo apt-get install dos2unix
    ```

3.  Download and install
    [miniconda](https://docs.conda.io/en/latest/miniconda.html) on the
    WSL

    Yes, do we have to perform this step (again) because WSL is a
    separate kernel and we need conda linux to be running there

4.  You are ready.

    Run `dos2unix make_venv.sh` to convert the shell script into Unix
    file format

    Run `bash make_venv.sh`

#### Using `Pyinstaller`

Always use `pyinstaller` on a dedicated virtual environment! This will
ensure that app will package the dependencies properly and minimise
debugging issues related to dependencies.

``` bash
# Using OSX
pyinstaller cli.py --name phdf --onefile --collect-all tables
```

#### Outdated instructions

Remote tester: `rbgv93k0001.int.osram-light.com`

On your local machine with internet access,

1.  Download latest Anaconda (python3.10) [Linux
    distribution](https://www.anaconda.com/download#downloads)

2.  Donwnload this repo using the `Download` button or `git clone`
    (don\'t forget to zip it for uploading)

3.  Transfer the 2 files into the Linux machine

4.  `sftp j.lim2@rbgv93k0001.int.osram-light.com`

5.  Check your remote dir using `sftp> pwd`

    ``` bash
    Remote working directory: /home/j.lim2/Downloads/
    ```

6.  Check your local dir `sftp> lpwd`

    ``` bash
    Local working directory: /Users/jli8/Downloads/
    ```

7.  Upload `Anaconda installer` using
    `sftp> put /Anaconda3-2023.03-1-Linux-x86_64.sh /Anaconda3-2023.03-1-Linux-x86_64.sh`

8.  Upload `phdf.tar` using `sftp> put /phdf-main.tar /phdf-main.tar`

Now, remote access into the linux machine

1.  Open `konsole`
2.  `cd ~/Downloads/`

First, install `Anaconda`

1.  `sh Anaconda3-2023.03-1-Linux-x86_64.sh`

2.  Follow the on screen instructions to install Anaconda

3.  Allow conda to `conda init`

4.  Run `conda info` command

    ``` bash
    active environment : base
    active env location : /home/j.lim2/Anaconda3
    conda version : 23.5.0
    python version : 3.10.9.final.0
    ```

Then, unpack `phdf-main` and start using it

1.  Unpack `phdf-main.tar`

2.  `cd /home/j.lim2/phdf-main`

3.  \[optional\] You can check if python interface is working properly

    ``` bash
    python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/Users/jli8/Downloads'

    INFO    : 0: appended(site1_partId_aTB_0) to  self.outpath.name='nil-20230607_093843-cp3.h5'
    ```

4.  Modify the path parameters in `phdf_j\Phdf.java`

    We need to modify the `Path` parameters, depending on your sys
    environment. In the future, when we figure out packaging and how to
    distribute, this part will be automated.

    ``` java
    public Phdf() {
        ...
        this.pythonPath = myDocPath + "/anaconda3/bin/python";
        this.cliPath = myDocPath + "/gitRepos/phdf/cli.py";
        ...
    }
    ```

5.  Modify the entry point `Main.java`

    This is just an example. This part code should be living in your
    actual test program.

    ``` java
    import phdf_j.Phdf;

    public class Main {

        public static void main(String[] args) {

            // Initialize the CLI tool
            Phdf processor = new Phdf();

            // Run the CLI tool (Option#1.1)
            processor.run(jsonString, "/Users/jli8/Downloads"); // Unfortunately, we get error=7, Argument list too long

            // Run the CLI tool (Option#1.2)
            processor.run("{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}", "/Users/jli8/Downloads");

            // Run the CLI tool (Option#2)
            processor.run("/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt", "/Users/jli8/Downloads");
        }

    }
    ```

6.  Test out the `java` entry point

    > ``` bash
    > (p311) ➜  200-phdf git:(wip) ✗ javac Main.java
    > (p311) ➜  200-phdf git:(wip) ✗ java Main
    >
    > command iniialized: [/Users/jli8/anaconda3/bin/python, /Users/jli8/gitRepos/phdf/cli.py]
    > PhdfProcess initialized
    > >> calling subprocess phdf (data.length=52) /Users/jli8/Downloads
    > INFO    : 0: appended(site1_partId1_aTB_0) to  self.outpath.name='nil-20230607_090809-cp3.h5'
    > >> phdf completed with exitCode=0
    > ```

7.  `sftp j.lim2@rbgv93k0001.int.osram-light.com`

8.  Check your remote dir using `sftp> pwd`

    ``` bash
    Remote working directory: /home/j.lim2/Downloads/
    ```

9.  Check your local dir `sftp> lpwd`

    ``` bash
    Local working directory: /Users/jli8/Downloads/
    ```

10. Upload `Anaconda installer` using
    `sftp> put /Anaconda3-2023.03-1-Linux-x86_64.sh /Anaconda3-2023.03-1-Linux-x86_64.sh`

11. Upload `phdf.tar` using `sftp> put /phdf-main.tar /phdf-main.tar`

Now, remote access into the linux machine

1.  Open `konsole`
2.  `cd ~/Downloads/`

First, install `Anaconda`

1.  `sh Anaconda3-2023.03-1-Linux-x86_64.sh`

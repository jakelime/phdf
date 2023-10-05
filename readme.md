# PHDF: Python HDF5 solution for Java

## Quick start

### (1) Simple example

#### Running directly using python

1. Clone the repo `git@gittf.ams-osram.info:os-opto-dev/phdf.git`
1. Run `python cli.p arg1 arg2`

```bash
# Use a JSON string
python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/Users/jli8/Downloads'

# Use a FileIO (a temporary file with JSON strings separated by commas)
python cli.py ~/phdf/resources/testfilewriter-2047225563688979.txt ~/Downloads
```

#### Running unittests

```bash
(py311) ➜  phdf git:(main) ✗ pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-7.4.2, pluggy-1.3.0 -- /Users/jakelim/anaconda3/envs/py311/bin/python
cachedir: .pytest_cache
rootdir: /Users/jakelim/SynologyDrive/cloud-active_project/phdf
plugins: dash-2.13.0
collected 4 items

tests/test_cli.py::test_cli_incomplete_calls[No args] PASSED             [ 25%]
tests/test_cli.py::test_cli_incomplete_calls[Missing args] PASSED        [ 50%]
tests/test_cli.py::test_cli[using JSON string] PASSED                    [ 75%]
tests/test_cli.py::test_cli[using FileIO] PASSED                         [100%]

============================== 4 passed in 3.72s ===============================
(py311) ➜  phdf git:(main) ✗
```

### (2) Full implementation

Although we can use this repository standalone, this is designed to be
built in as a depedency using `git submodule`.

```bash
git clone --recurse-submodules git@gitlab.private.info:privatedevs/distribute_smt8.git
python push.py --push
```

Both `Smartest TestProgram` and `PHDF` (latest versions) will be pushed to the server
automically.

Just run the `TestProgram` after you push, that is all.

To improve further, we can compile a distributable app with syslink to system path `phdf`, then run

```bash
# command line interface: phdf arg1 arg2
phdf ~/phdf/resources/testfilewriter-2047225563688979.txt ~/Downloads
```

## Details

### Basics

PHDF is a CLI(command line interface) tool that takes in 2 arguments

1. **data_input**

   accept a filepath, or `JSON` string in a specific format.

1. **output_dir**

   accept a file directory. Exception will be raised if dir does not
   exist.

Notes:

1. _JSON String format_

   Must be a string that in this format:
   `{"partId": {"R00C00": {"site1":{"aTB_0": "0.0"}}}}`

   Multiple JSON strings can be separated by commas
   `{"partId": {"R00C00": {"site1":{"aTB_0": "0.0"}}}}, {"partId": {"R00C01": {"site1":{"aTB_0": "0.0"}}}}`

1. Do take care of the double quotes `"` and single quotes `'`.

   - `Java` specifies that `String` must be enclosed with `"`
   - `JSON` specifies that `key` and `values` must be enclosed with `"`
   - In `python`, `"` or `'` can be interchanged with flexibility
   - In `bash`, `'` means literal strings, we can use it to encase like this `'{"a": "1"}'`

### Advanced Options

PHDF is a fully implemented CLI tool, you can use --help flag to display
options and help information.

```bash
 ➜  200-phdf git:(main) ✗ python cli.py -h
usage: phdf [-h] [-scu] [-mt] data_input output_dir

Process given data into hdf5 container

positional arguments:
  data_input            Accepts 'filepath' |or| 'dataString' in JSON format
  output_dir            Output directory

options:
  -h, --help            show this help message and exit
  -scu, --skip_cleanup  Skips clean up of the temporary.txt files
  -mt, --measure_timing
                        Measures time taken for the python process calls

Example: python cli.py '{"partId": {"R00C00": { "site1":{"aTB_0": "0.0"}}}}' '/tmp/sample.h5'
```

--measure_timing

```bash
(p311) ➜  200-phdf git:(cleanup) ✗ java Main
intiailised filepath = /Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt
PhdfProcess initialized
command iniialized: /Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py, --measure_timing
 >> calling subprocess phdf {"partId1": {"R00C00": { "site1":{"aTB_0": "0.0"}}}} /Users/jli8/Downloads
INFO    : 0: appended(site1_partId1_aTB_0) to  nil-20230621_141921-cp3.h5
INFO    : ***** PHDF_time_taken = 0.1903s *****

command iniialized: [/Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py, --measure_timing]
 >> calling subprocess phdf /Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt /Users/jli8/Downloads
INFO    : 0: appended(site1_partId1_aTB_0) to  testfilewriter-2047225563688979-cp3.h5
...
INFO    : 19: appended(site2_partId1_aTB_9) to  testfilewriter-2047225563688979-cp3.h5
INFO    : ***** PHDF_time_taken = 3.3210s *****
```

--skip_cleanup

By default, the current implementation is that Smartest TestProgram will create a
temporary file `testfilewriter-2047225563688979-cp3.txt`, then PHDF will read that file to record the
HDF5 output. PHDF will perform clean up by deleting the temporary file. You can skip removing the
temporary file by using the `-scs` option. Do note that the HDD will quickly get filled
up because `.txt` is a very inefficient storage container.

### Interfacing to Java using subprocess to call python

We will use Java's
`ProcessBuilder builder = new ProcessBuilder(command);`,

A simple example of how to implement:

- `Main.java` is the entry point to call `Phdf.java`
- `Phdf` java class is a process builder/manager to a create a new process instance
- We use this instance a subprocess thread using the shell, `python cli.py arg1 arg2`

A simple execution example:

```java
public static void main(String[] args) {

    Phdf processor = new Phdf();
    processor.run("{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}", "/Users/jli8/Downloads");

}
```

Output:

```bash
 ➜  200-phdf git:(wip) ✗ javac Main.java
 ➜  200-phdf git:(wip) ✗ java Main
PhdfProcess initialized
command initialized, /Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py
>> calling subprocess phdf (data.length=52) /Users/jli8/Downloads
INFO    : 0: appended(site1_partId1_aTB_0) to 'nil-20230607_090809-cp3.h5'
>> phdf completed with exitCode=0
```

### Notes

Unfortunately, we will face problems if we try to pass the entire
`JSON string` into the command. The length of the string is too long
(`length=1356801`), which gives us `error=7, Argument list too long`.

To fix this problem, we the data to a file using `FileIO`, then pass the
filepath to the command line.

```java
import lib.shared.common.util.CustomFileWriter;
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

```bash
 ➜  phdf git:(wip) ✗ javac Main.java
 ➜  phdf git:(wip) ✗ java Main
intiailised filepath = /Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt
command initialized: /Users/jli8/miniconda3/envs/p311/bin/python, /Users/jli8/activedir/200-phdf/cli.py
>> calling subprocess phdf
INFO    : 0: appended(site1_partId1_aTB_0) to 'testfilewriter-2047225563688979-cp3.h5'
INFO    : 1: appended(site1_partId1_aTB_1) to 'testfilewriter-2047225563688979-cp3.h5'
...
INFO    : 18: appended(site2_partId1_aTB_8) to 'testfilewriter-2047225563688979-cp3.h5'
INFO    : 19: appended(site2_partId1_aTB_9) to 'testfilewriter-2047225563688979-cp3.h5'
>> phdf completed with exitCode=0
```

## Environment Setup and Installation

```bash
➜  phdf git:(main) ✗ python -m venv venv
➜  phdf git:(main) ✗ source venv/bin/activate
(venv) ➜  phdf git:(main) ✗ pip install -r requirements.txt
(venv) ➜  phdf git:(main) ✗ python cli.py
```

### Using `Pyinstaller`

Always use `pyinstaller` on a virtual environment from `python -m venv venv`

Use this to create a binary application for `cli`.

```bash
(venv) ➜  phdf git:(main) ✗ pip install pyinstaller
(venv) ➜  phdf git:(main) ✗ pyinstaller cli.py --name phdf --onefile --collect-all tables
```

## Changelogs

- v1.1.0

  - updated readme
  - updated PHDF core codes (tidy up)
  - updated test to work with new codes
  - added new CLI arguments
    - skip_cleanup
    - measure_timing
  - cleaned up Java entry points, for better doucmentation

- v1.0.5

  - added push.py for DevOps

- v1.0.3

  - added pytest, with a total of 4 critical basic tests
    - 2 tests to CLI for invalid arguments given
    - test to CLI using JSON string
    - test to CLI using File as input

- v1.0.2

  - updated readme
  - updated java codes and entry points

- v1.0.0 / v1.0.1

  - Properly structured into `models.py`, `views.py` and `main.py`
    (presenter)
  - Entry point will be `cli.py` where it calls \"launcher\" from
    `presenter`
  - `cli.py` reworked with `argparse` for fully supported CLI with
    help and instructions
  - `tests.py` structured to be used for code testing
  - `views.py` primary function is to interact the data, view
    dataframe and plot pixelMaps
  - `models.py` defines the working model, data structures of our
    device

- v0.0.2

  - Packaged java class `Phdf` into a separate package
  - `Main.java` will be an entry point to instantiate `process`
    object, then call `process.run()` method to execute

- v0.0.3

  - Worked out some kinks during debugging when integrating into
    SMT8
  - `Phdf.java`: some hard-coded variables are now changed to match
    environment of `rbgv93k0001.int.osram-light.com`

- v0.0.1
  - first draft version released

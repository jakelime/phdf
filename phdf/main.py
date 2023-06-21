import time
from pathlib import Path

from phdf import models
from phdf.utils import setup_logger

log = setup_logger()


def launcher_json_string(
    data_input: str, output_dir: str, measure_timing: bool = False
):
    assert isinstance(data_input, str)
    if measure_timing:
        start_time = time.perf_counter()
    dpx = models.DevicePixelArray(inp=data_input, output_folder=output_dir)
    dpx.run()
    dpx.save_to_hdf()
    if measure_timing:
        elapsed_time = time.perf_counter() - start_time  # type: ignore
        log.info(f"{'*'*5} PHDF_time_taken = {elapsed_time:.4f}s {'*'*5}")
    return 0


def launcher_fileio(
    data_input: str,
    output_dir: str,
    skip_cleanup: bool = False,
    measure_timing: bool = False,
):
    fp = Path(data_input)
    assert fp.is_file()
    if measure_timing:
        start_time = time.perf_counter()
    dpx = models.DevicePixelArray(inp=fp, output_folder=output_dir)
    dpx.run()
    dpx.save_to_hdf()

    if skip_cleanup:
        dpx.cleanup()
    else:
        log.info("skipped cleanup")

    if measure_timing:
        elapsed_time = time.perf_counter() - start_time  # type: ignore
        log.info(f"{'*'*5} PHDF_time_taken = {elapsed_time:.4f}s {'*'*5}")

    return 0

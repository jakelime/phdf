from pathlib import Path

from phdf import models


def launcher_json_string(data_input, output_dir):
    assert isinstance(data_input, str)
    dpx = models.DevicePixelArray(inp=data_input, output_folder=output_dir)
    dpx.run()
    dpx.save_to_hdf()
    return 0

def launcher_fileio(data_input, output_dir, skip_cleanup=False):
    fp = Path(data_input)
    assert fp.is_file()
    dpx = models.DevicePixelArray(inp=fp, output_folder=output_dir)
    dpx.run()
    dpx.save_to_hdf()
    if skip_cleanup:
        dpx.cleanup()
    return 0

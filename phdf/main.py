from pathlib import Path
APP_NAME = "phdf"

# local libraries
if __name__.startswith(APP_NAME):
    from . import utils
    from . import models
else:
    import utils
    import models


def launcher_json_string(data_input, output_dir):
    assert isinstance(data_input, str)
    dpx = models.DevicePixelArray(inp=data_input, output_folder=output_dir)  # type: ignore
    dpx.run()
    dpx.save_to_hdf()
    return 0

def launcher_fileio(data_input, output_dir):
    fp = Path(data_input)
    assert fp.is_file()
    dpx = models.DevicePixelArray(inp=fp, output_folder=output_dir)  # type: ignore
    dpx.run()
    dpx.save_to_hdf()
    dpx.cleanup()
    return 0

if __name__ == "__main__":
    log = utils.setup_logger()
    log.error("Not implemented. Please use cli instead")

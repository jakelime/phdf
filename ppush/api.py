from __future__ import annotations
import time
import logging
from typing import Optional
from pathlib import Path
import platform
import subprocess

APP_NAME = "phdf"


class FileManager:
    def __init__(self):
        self.log = setup_logger(APP_NAME)
        self.cwd = Path(__file__).parent

    def go_up(self) -> FileManager:
        self.cwd = self.cwd.parent
        return self

    def get_cwd(self) -> Path:
        return self.cwd

    def cd(self, foldername: str) -> FileManager:
        path = self.cwd / foldername
        if path.is_dir():
            self.cwd = path
        else:
            self.log.error(f"invalid {foldername=}")
        return self

    def find_file(self, filename: str, single_file: bool = False) -> list | Path:
        filepaths = self.cwd.glob(filename)
        if single_file:
            return next(filepaths)
        else:
            return [x for x in filepaths]

    def get_resource_file(self, use_wildcard: str | bool = False) -> Path:
        self.go_up().cd("resources")
        if use_wildcard:
            return self.find_file(use_wildcard, single_file=True)  # type: ignore
        else:
            raise NotImplementedError(f"{use_wildcard=}")


def setup_logger(
    logger_name: Optional[str] = None, default_level: str = "INFO"
) -> logging.Logger:
    """Creates a basic logger object, logging to console

    :param logger_name: _description_, defaults to None
    :type logger_name: str, optional
    :param default_level: _description_, defaults to "INFO"
    :type default_level: str, optional
    :return: _description_
    :rtype: logging.Logger
    """

    if logger_name is None:
        logger_name = APP_NAME
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        return logger

    console_format = logging.Formatter("%(levelname)-8s: %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(default_level)
    console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)
    logger.setLevel(default_level)
    return logger


def get_logger_level_bool(level: int = 10) -> bool:
    logger = logging.getLogger(APP_NAME)
    return logger.getEffectiveLevel() <= level


def console_out(
    outpath, txtstr: str = "saved", level: str = "INFO", prefix: str = ""
) -> None:
    """log to console using a template format

    :param outpath: _description_
    :type outpath: _type_
    :param txtstr: _description_, defaults to "saved"
    :type txtstr: str, optional
    :param level: _description_, defaults to "INFO"
    :type level: str, optional
    :param prefix: _description_, defaults to ""
    :type prefix: str, optional
    """
    log = logging.getLogger(APP_NAME)
    ostr = f"{prefix}{txtstr} //{outpath.parent.name}/{outpath.name}"
    match level.upper():
        case "INFO":
            log.info(ostr)
        case "DEBUG":
            log.debug(ostr)
        case "CRITICAL":
            log.critical(ostr)
        case "WARNING":
            log.warning(ostr)
        case _:
            print(ostr)


def get_time(datetimestrformat: str = "%Y%m%d_%H%M%S"):
    """
    Returns the datetime string at the time of function call
    :param datetimestrformat: datetime string format, defaults to "%Y%m%d_%H%M%S"
    :type datetimestrformat: str, optional
    :return: datetime in string format
    :rtype: str
    """
    return time.strftime(datetimestrformat, time.localtime(time.time()))


def get_python_path() -> str:
    python_path = Path(".")
    current_os = platform.system()
    for py in ["python", "python3"]:
        match current_os:
            case "Darwin" | "Linux":
                p0 = subprocess.run(
                    [
                        "which",
                        py,
                    ],
                    capture_output=True,
                )
            case "Windows":
                p0 = subprocess.run(
                    [
                        "where.exe",
                        py,
                    ],
                    capture_output=True,
                )
            case _:
                raise NotImplementedError(f"{current_os=} is not supported")
        python_path = p0.stdout.decode("utf-8").split("\n")[0].strip()
        python_path = Path(python_path)
        if python_path.is_file():
            break
    if not python_path.is_file():
        raise PtConfigError("could not find python exe")

    return str(python_path.absolute())


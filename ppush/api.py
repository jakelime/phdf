import time


def get_time(datetimestrformat: str = "%Y%m%d_%H%M%S"):
    """
    Returns the datetime string at the time of function call
    :param datetimestrformat: datetime string format, defaults to "%Y%m%d_%H%M%S"
    :type datetimestrformat: str, optional
    :return: datetime in string format
    :rtype: str
    """
    return time.strftime(datetimestrformat, time.localtime(time.time()))

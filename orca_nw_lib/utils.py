import os
import platform
import subprocess
import yaml
import logging
import logging.config
import yaml
from .constants import conn_timeout

_settings = {}
abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)


def get_orca_config(orca_config_file: str = f"{dname}/orca.yml"):
    """
    Read the Orca configuration file and return the parsed settings.

    Parameters:
        orca_config_file (str, optional): The path to the Orca configuration file.
            Defaults to "./orca.yml".

    Returns:
        dict: The parsed settings from the Orca configuration file.
    """
    global _settings
    if not _settings:
        with open(orca_config_file, "r") as stream:
            try:
                _settings = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    return _settings


_logging_initialized: bool = False


def get_logging(logging_config_file: str = f"{dname}/logging.yml"):
    """
    Initializes the logging configuration and returns the logging module.

    Parameters:
        logging_config_file (str): The path to the logging configuration file.
            Defaults to "./logging.yml".

    Returns:
        logging: The logging module.
    """
    global _logging_initialized
    if not _logging_initialized:
        with open(logging_config_file, "r") as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            logging.config.dictConfig(config) if config else print(
                "Error occurred while loading ORCA logging config."
            )
        _logging_initialized = True
    return logging


def ping_ok(device_ip) -> bool:
    """
    Checks if a device is reachable by sending a ping request.

    Args:
        device_ip (str): The IP address of the device to ping.

    Returns:
        bool: True if the ping request was successful, False otherwise.
    """
    
    try:
        subprocess.check_output(
            f'ping -{"n" if platform.system().lower() == "windows" else "c"} 1 -t {get_orca_config().get(conn_timeout)} {device_ip}',
            shell=True,
        )
    except Exception:
        return False
    return True

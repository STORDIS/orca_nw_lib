import os
import platform
import subprocess
import yaml
import logging.config
import logging
from .constants import conn_timeout
from orca_nw_lib.constants import neo4j_url, neo4j_password, neo4j_user, protocol
from neomodel import config, db, clear_neo4j_database

_settings = {}
abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)

orca_config_loaded = False

def get_config_status():
    return orca_config_loaded

def load_orca_config(
    orca_config_file: str = f"{dname}/orca.yml",
    logging_config_file: str = f"{dname}/logging.yml",
    force_reload=False,
):
    global orca_config_loaded
    if force_reload or not orca_config_loaded:
        load_orca_config_from_file(orca_config_file=orca_config_file)
        init_db_connection()
        get_logging(logging_config_file=logging_config_file)
        orca_config_loaded = True


def init_db_connection():
    config.DATABASE_URL = f"{_settings.get(protocol)}://{_settings.get(neo4j_user)}:{_settings.get(neo4j_password)}@{_settings.get(neo4j_url)}"


def clean_db():
    clear_neo4j_database(db)

def get_orca_config():
    return _settings

def load_orca_config_from_file(orca_config_file: str = f"{dname}/orca.yml", force_reload=False):
    """
    Read the Orca configuration file and return the parsed settings.

    Parameters:
        orca_config_file (str, optional): The path to the Orca configuration file.
            Defaults to "./orca.yml".

    Returns:
        dict: The parsed settings from the Orca configuration file.
    """
    global _settings
    if force_reload or not _settings:
        with open(orca_config_file, "r") as stream:
            try:
                _settings = yaml.safe_load(stream)
                print("Loaded ORCA config from {0}".format(orca_config_file))
            except yaml.YAMLError as exc:
                print(exc)
    return _settings


_logging_initialized: bool = False


def get_logging(logging_config_file: str = f"{dname}/logging.yml", force_reload=False):
    """
    Initializes the logging configuration and returns the logging module.

    Parameters:
        logging_config_file (str): The path to the logging configuration file.
            Defaults to "./logging.yml".

    Returns:
        logging: The logging module.
    """
    global _logging_initialized
    if force_reload or not _logging_initialized:
        with open(logging_config_file, "r") as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            if config:
                logging.config.dictConfig(config)
                print("Loaded ORCA logging config from {0}".format(logging_config_file))
            else:
                print(
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

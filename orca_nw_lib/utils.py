import os
import platform
import subprocess
import yaml
import logging
import logging.config
from pathlib import Path
import yaml
from .constants import conn_timeout

_settings={}
abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)

def get_orca_config(orca_config_file:str=f"{dname}/orca.yml"):
    global _settings
    if not _settings:
        with open(orca_config_file, "r") as stream:
            try:
                _settings=yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    return _settings

_logging_initialized:bool=False
def get_logging(logging_config_file:str=f'{dname}/logging.yml'):
    global _logging_initialized
    if not _logging_initialized:
        with open(logging_config_file, 'r') as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            logging.config.dictConfig(config) if config else print('Error occurred while loading ORCA logging config.')
        _logging_initialized=True
    return logging

def ping_ok(sHost) -> bool:
    try:
        subprocess.check_output(
            f'ping -{"n" if platform.system().lower() == "windows" else "c"} 1 -t {get_orca_config().get(conn_timeout)} {sHost}', shell=True
        )
    except Exception:
        return False
    return True

get_logging()
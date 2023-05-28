import os
import platform
import subprocess
import yaml
import logging
import logging.config
from pathlib import Path
import yaml
from .constants import conn_timeout

settings={}


def load_default_orca_config():
    abspath = os.path.abspath(__file__)
    # Absolute directory name containing this file
    dname = os.path.dirname(abspath)
    load_logging_config(f'{dname}/logging.yml')
    load_config(f"{dname}/orca.yml")


def load_config(orca_config_file):
    global settings
    if not settings:
        with open(orca_config_file, "r") as stream:
            try:
                settings=yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    return settings


def load_logging_config(logging_config_file):
    with open(logging_config_file, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)


def ping_ok(sHost) -> bool:
    try:
        subprocess.check_output(
            f'ping -{"n" if platform.system().lower() == "windows" else "c"} 1 -t {settings.get(conn_timeout)} {sHost}', shell=True
        )
    except Exception:
        return False
    return True

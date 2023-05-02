import os
import yaml
import logging
import logging.config
from pathlib import Path
import yaml

settings={}

def load_orca_config():
    abspath = os.path.abspath(__file__)
    # Absolute directory name containing this file
    dname = os.path.dirname(abspath)
    load_logging_config()
    load_config(f"{dname}/")

def load_config(dname):
    global settings
    if not settings:
        with open(f"{dname}/orca.yml", "r") as stream:
            try:
                settings=yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    return settings

def load_logging_config():
    base_path = Path(__file__).parent
    file_path = (base_path / "./logging.yml").resolve()
    with open(file_path, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)

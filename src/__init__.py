import logging
import logging.config
from pathlib import Path
import yaml
from utils import load_config,dname
base_path = Path(__file__).parent
file_path = (base_path / "../logging.yml").resolve()
with open(file_path, 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)
logging.config.dictConfig(config)

load_config(dname)

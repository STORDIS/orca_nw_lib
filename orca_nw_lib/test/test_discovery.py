import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_config, load_logging_config
load_config()
load_logging_config()
from orca_nw_lib.discovery import discover_all
discover_all()
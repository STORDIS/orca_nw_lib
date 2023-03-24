from orca_backend.utils import load_config, load_logging_config
import os

abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
load_logging_config()
load_config(f"{dname}/../")

from orca_backend.gnmi_util import discover_topology
discover_topology()

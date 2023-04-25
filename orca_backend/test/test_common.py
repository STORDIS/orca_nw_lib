from orca_backend.utils import load_config, load_logging_config
import os

dut_ip="10.10.131.111"

def load_orca_config():
    abspath = os.path.abspath(__file__)
    # Absolute directory name containing this file
    dname = os.path.dirname(abspath)
    load_logging_config()
    load_config(f"{dname}/../")
    




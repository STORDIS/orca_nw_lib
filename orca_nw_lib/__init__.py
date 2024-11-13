from orca_nw_lib.gnmi_sub import gnmi_subscribe_for_all_devices_in_db
from orca_nw_lib.utils import load_orca_config
from orca_nw_lib.influxdb_utils import load_influxdb_config
from . import constants as const
import os
import yaml

abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
# read env var or set default
default_orca_nw_lib_config = os.environ.get(
    const.env_default_orca_nw_lib_config_file, f"{dname}/orca_nw_lib.yml"
)

# Load configuration from YAML file
with open(default_orca_nw_lib_config, 'r') as file:
    try:
        config = yaml.safe_load(file)
        if config.get('live_monitoring', False):
            load_influxdb_config()
    except yaml.YAMLError as exc:
        print(exc)



load_orca_config()

## Also subscribe for gnmi events for all devices already discovered in the database.
## This is the case when devices are already discovered but the application is restarted, due to any reason.
gnmi_subscribe_for_all_devices_in_db()

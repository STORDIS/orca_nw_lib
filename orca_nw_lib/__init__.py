from orca_nw_lib.gnmi_sub import gnmi_subscribe_for_all_devices_in_db
from orca_nw_lib.utils import get_telemetry_db, load_orca_config
from orca_nw_lib.promdb_utils import load_prometheus_config
from orca_nw_lib.influxdb_utils import load_influxdb_config



# Load configuration from YAML file
settings = load_orca_config()

# Loads influxdb configs
if get_telemetry_db() == "influxdb":
    load_influxdb_config(settings)

# Loads prometheus configs
if get_telemetry_db() == "prometheus":
    load_prometheus_config(settings)

## Also subscribe for gnmi events for all devices already discovered in the database.
## This is the case when devices are already discovered but the application is restarted, due to any reason.
gnmi_subscribe_for_all_devices_in_db()

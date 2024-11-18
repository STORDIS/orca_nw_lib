from orca_nw_lib.gnmi_sub import gnmi_subscribe_for_all_devices_in_db
from orca_nw_lib.utils import check_live_monitoring, load_orca_config
from orca_nw_lib.influxdb_utils import load_influxdb_config

load_orca_config()

if check_live_monitoring():
    load_influxdb_config()

## Also subscribe for gnmi events for all devices already discovered in the database.
## This is the case when devices are already discovered but the application is restarted, due to any reason.
gnmi_subscribe_for_all_devices_in_db()

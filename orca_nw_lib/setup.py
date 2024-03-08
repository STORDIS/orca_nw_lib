from orca_nw_lib.utils import  get_logging, init_db_connection, load_orca_config_from_file, default_orca_nw_lib_config, default_logging_config
from orca_nw_lib.gnmi_sub import gnmi_subscribe_for_all_devices_in_db
orca_config_loaded = False

def setup(
    orca_config_file: str = default_orca_nw_lib_config,
    logging_config_file: str = default_logging_config,
    force_reload=False,
):
    global orca_config_loaded
    print("Loading ORCA config from {0}".format(orca_config_file))
    print("Loading ORCA logging config from {0}".format(logging_config_file))
    
    if force_reload or not orca_config_loaded:
        load_orca_config_from_file(orca_config_file=orca_config_file,force_reload=force_reload)
        init_db_connection()
        get_logging(logging_config_file=logging_config_file,force_reload=force_reload)
        orca_config_loaded = True
    ## Also subscribe for gnmi events for all devices already discovered in the database.
    ## This is the case when devices are already discovered but the application is restarted, due to any reason.
    
    gnmi_subscribe_for_all_devices_in_db()

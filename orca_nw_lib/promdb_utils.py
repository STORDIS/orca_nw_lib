""" Utils for Prometheus """

import os
from prometheus_client import CollectorRegistry, push_to_gateway
import yaml
from . import constants as const

_settings = {}

# prometheus client
_prometheus_url = None

_prometheus_monitoring = False

abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
# read env var or set default
default_orca_nw_lib_config = os.environ.get(
    const.env_default_orca_nw_lib_config_file, f"{dname}/orca_nw_lib.yml"
)
default_logging_config = os.environ.get(
    const.env_default_logging_config_file, f"{dname}/orca_nw_lib_logging.yml"
)


def is_prometheus_monitoring():
    global _prometheus_monitoring
    return _prometheus_monitoring


def init_prometheus_client():
    """
    Initialize prometheus client
    Returns:
        Prometheus Client object http://localhost:9091/metrics/job/pushgateway
    """
    global _prometheus_url
    _prometheus_url = f"http://{os.environ.get(const.promdb_pushgateway_url, _settings.get(const.promdb_pushgateway_url))}/metrics/job/{os.environ.get(const.promdb_job, _settings.get(const.promdb_job))}"
    return _prometheus_url



def write_to_prometheus(registry: CollectorRegistry):
    """
    Pushes data to the prometheus pushgateway.

    Args:
        registry (CollectorRegistry): Collections of metrices like gauge, Info etc.
    Returns:
        None
    """
    push_to_gateway(
        _prometheus_url, 
        job= os.environ.get(const.promdb_job, _settings.get(const.promdb_job)), 
        registry= registry
    )
    



def load_prometheus_config(orca_settings):
    """
    Gets Orca configuration and return the parsed settings.

    Parameters:
        orca_settings (dict): Orca config in key, value pairs.

    Returns:
        dict: The parsed settings from the Orca configuration file.
    """
    global _settings, _prometheus_monitoring
    if not _settings:
        try:
            _settings = orca_settings
            print("Loaded Prometheus config.")
        except yaml.YAMLError as exc:
                print(exc)
        init_prometheus_client()
        _prometheus_monitoring = True
    return _settings


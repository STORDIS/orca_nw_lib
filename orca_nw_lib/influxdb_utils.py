""" Utils for Influx DB """

import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import yaml
from . import constants as const

_settings = {}

# influxDB client
_influxdb_client = None

_influxdb_monitoring = False

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


def is_influxdb_monitoring():
    return _influxdb_monitoring


def init_influxdb_client():
    """
    Initialize Influxdb client

    Returns:
        Influxdb client obj
    """
    global _influxdb_client
    _influxdb_client = InfluxDBClient(
        url= f"http://{os.environ.get(const.influxdb_url, _settings.get(const.influxdb_url))}",
        token= os.environ.get(const.influxdb_token, _settings.get(const.influxdb_token)),
        org= os.environ.get(const.influxdb_org, _settings.get(const.influxdb_org))
        )


def get_influxdb_client():
    """
    Returns the initialized InfluxDB client.
    
    Returns:
        InfluxDB Client: The client for InfluxDB.
    """
    global _influxdb_client
    return _influxdb_client


def create_point(metric_name):
    """
    Create a new InfluxDB Point object for the specified metric.

    Args:
        metric_name (str): The name of the metric to be recorded in InfluxDB.

    Returns:
        Point: An InfluxDB Point object initialized with the given metric name.
    """
    return Point(metric_name)


def get_write_api():
    """
    Returns the write API for the InfluxDB client.

    This function retrieves the initialized InfluxDB client and returns its write API,
    which can be used to write data points to the InfluxDB database. 

    Returns:
        WriteApi: The write API for the InfluxDB client.
    """
    client = get_influxdb_client()
    return client.write_api(write_options=SYNCHRONOUS)


def write_to_influx(point):
    """
    Write a data point to the specified InfluxDB bucket.

    Args:
        point (Point): The InfluxDB Point object to be written.
    Returns:
        None
    """
    bucket = os.environ.get(const.influxdb_bucket, _settings.get(const.influxdb_bucket))
    write_api = get_write_api()
    write_api.write(bucket=bucket, record=point, org=os.environ.get(const.influxdb_org, _settings.get(const.influxdb_org)))




def load_influxdb_config(orca_settings):
    """
    Gets Orca configuration and return the parsed settings.

    Parameters:
        orca_settings (dict): Orca config in key, value pairs.

    Returns:
        dict: The parsed settings from the Orca configuration file.
    """
    global _settings, _influxdb_monitoring
    if not _settings:
        try:
            _settings = orca_settings
            print("Loaded InfluxDB config.")
        except yaml.YAMLError as exc:
            print(exc)
        init_influxdb_client()
        _influxdb_monitoring = True
    return _settings


""" Utils for Influx DB """

import os
import re
import ipaddress
import logging.config
import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
import yaml
from . import constants as const

_settings = {}

# influxDB client
_influxdb_client = None

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


def init_influxdb_client():
    """
    Initialize Influxdb client

    Args:
        metric_name: Name of the point or data in InfluxDB (eg: interface, bgp, mclag).

    Returns:
        Influxdb Point obj
    """
    global _influxdb_client
    _influxdb_client = InfluxDBClient(
        url= os.environ.get(const.influxdb_url, _settings.get(const.influxdb_url)),
        token= os.environ.get(const.influxdb_token, _settings.get(const.influxdb_token)),
        org= os.environ.get(const.influxdb_org, _settings.get(const.influxdb_org))
        )


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


def get_influxdb_client():
    """
    Returns the initialized InfluxDB client.
    
    Returns:
        InfluxDB Client: The client for InfluxDB.
    """
    global _influxdb_client
    return _influxdb_client


def load_influxdb_config(orca_config_file: str = default_orca_nw_lib_config):
    """
    Read the Orca configuration file and return the parsed settings.

    Parameters:
        orca_config_file (str, optional): The path to the Orca configuration file.
            Defaults to "./orca.yml".

    Returns:
        dict: The parsed settings from the Orca configuration file.
    """
    global _settings
    if not _settings:
        with open(orca_config_file, "r") as stream:
            try:
                _settings = yaml.safe_load(stream)
                print("Loaded InfluxDB config from {0}".format(orca_config_file))
            except yaml.YAMLError as exc:
                print(exc)
        init_influxdb_client()
    return _settings


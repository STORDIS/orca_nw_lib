""" Utils for Influx DB """

from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from orca_nw_lib.utils import get_influxdb_bucket, get_influxdb_client, get_influxdb_org


def create_point(metric_name):
    """
    Create a new InfluxDB Point object for the specified metric.

    Args:
        metric_name (str): The name of the metric to be recorded in InfluxDB.

    Returns:
        Point: An InfluxDB Point object initialized with the given metric name.
    """
    return Point(metric_name)


def write_to_influx(point):
    """
    Write a data point to the specified InfluxDB bucket.

    Args:
        point (Point): The InfluxDB Point object to be written.
    Returns:
        None
    """
    client = get_influxdb_client()
    bucket = get_influxdb_bucket()
    org = get_influxdb_org()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, record=point, org= org)
    


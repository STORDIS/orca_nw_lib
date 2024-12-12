""" Utils for Prometheus """

from prometheus_client import CollectorRegistry, push_to_gateway
from orca_nw_lib.utils import get_prometheus_job, get_prometheus_url


def write_to_prometheus(registry: CollectorRegistry = None):
    """
    Pushes data to the prometheus pushgateway.

    Args:
        registry (CollectorRegistry): Collections of metrices like gauge, Info etc.
    Returns:
        None
    """
    push_to_gateway(
         gateway= get_prometheus_url(), 
        job= get_prometheus_job(), 
        registry= registry
    )

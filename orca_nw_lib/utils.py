""" Utils for ORCA Network Library """

import os
import re
import ipaddress
import logging.config
import logging
from neomodel import config, db, clear_neo4j_database
import yaml
from . import constants as const

_settings = {}
abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
# read env var or set default
default_orca_nw_lib_config = os.environ.get(
    "ORCA_NW_LIB_CONFIG_FILE", f"{dname}/orca_nw_lib.yml"
)
default_logging_config = os.environ.get(
    "ORCA_NW_LIB_LOGGING_CONFIG_FILE", f"{dname}/orca_nw_lib_logging.yml"
)


def init_db_connection():
    config.DATABASE_URL = f"{_settings.get(const.protocol)}://{_settings.get(const.neo4j_user)}:{_settings.get(const.neo4j_password)}@{_settings.get(const.neo4j_url)}"


def clean_db():
    clear_neo4j_database(db)


def get_networks():
    global _settings
    return _settings.get(const.networks)


def get_device_cred(device_ip):
    for addr, cred in get_networks().items():
        if device_ip in [str(ip) for ip in ipaddress.ip_network(addr)]:
            return cred


def get_conn_timeout():
    return _settings.get(const.conn_timeout)


def get_device_password():
    return _settings.get(const.password)


def get_device_username():
    return _settings.get(const.username)


def get_device_grpc_port():
    return _settings.get(const.grpc_port)


def load_orca_config(orca_config_file: str = default_orca_nw_lib_config):
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
                print("Loaded ORCA config from {0}".format(orca_config_file))
            except yaml.YAMLError as exc:
                print(exc)
        init_db_connection()
    return _settings


_logging_initialized: bool = False


def get_logging(logging_config_file: str = default_logging_config):
    """
    Initializes the logging configuration and returns the logging module.

    Parameters:
        logging_config_file (str): The path to the logging configuration file.
            Defaults to "./logging.yml".

    Returns:
        logging: The logging module.
    """
    global _logging_initialized
    if not _logging_initialized:
        with open(logging_config_file, "r") as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            if config:
                logging.config.dictConfig(config)
                print("Loaded ORCA logging config from {0}".format(logging_config_file))
            else:
                print("Error occurred while loading ORCA logging config.")
        _logging_initialized = True
    return logging


import socket
import time

_logger = get_logging().getLogger(__name__)


def ping_ok(host, max_retries=1):
    retry = 0
    status = False
    port = get_device_grpc_port()
    while retry < max_retries:
        # Create a TCP socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(get_conn_timeout())
            sock.connect((host, port))
            status = True
            break
        except socket.error as e:
            _logger.error("Failed to connect to %s on port %s: %s", host, port, e)
            retry += 1
            status = False
            time.sleep(1)  # Wait before retrying
        finally:
            sock.close()
            return status



def validate_and_get_ip_prefix(network_address:str):
    """
    Validates and extracts the IP prefix from a given network address.

    Args:
        network_address (str): The network address to validate and extract the IP prefix from.

    Returns:
        Tuple[str, str, int] or Tuple[None, None, None]: A tuple containing the network address, the IP address, and the prefix length.
        If the network address is invalid, returns (None, None, None).
    """
    try:
        ip_network = ipaddress.ip_network(network_address, strict=False)
        return (
            (
                network_address.split(match.group(), 1)[0]
                if (match := re.search("/", network_address))
                else network_address
            ),
            str(ip_network.network_address),
            ip_network.prefixlen
        )
    except ValueError:
        _logger.error(f"Invalid network address: {network_address}")
        return None, None, None

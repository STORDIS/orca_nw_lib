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
    const.env_default_orca_nw_lib_config_file, f"{dname}/orca_nw_lib.yml"
)
default_logging_config = os.environ.get(
    const.env_default_logging_config_file, f"{dname}/orca_nw_lib_logging.yml"
)


def init_db_connection():
    config.DATABASE_URL = f"{os.environ.get(const.neo4j_protocol, _settings.get(const.neo4j_protocol))}://{os.environ.get(const.neo4j_user, _settings.get(const.neo4j_user))}:{os.environ.get(const.neo4j_password, _settings.get(const.neo4j_password))}@{os.environ.get(const.neo4j_url, _settings.get(const.neo4j_url))}"


def clean_db():
    clear_neo4j_database(db)


def get_networks():
    return (
        networks.split(",")
        if (networks := os.environ.get(const.discover_networks))
        else _settings.get(const.discover_networks)
    )


def get_request_timeout():
    return int(
        os.environ.get(
            const.request_timeout, _settings.get(const.request_timeout)
        )
    )


def get_ping_timeout():
    return int(
        os.environ.get(
            const.ping_timeout, _settings.get(const.ping_timeout)
        )
    )


def get_device_password():
    return os.environ.get(const.device_password, _settings.get(const.device_password))


def get_device_username():
    return os.environ.get(const.device_username, _settings.get(const.device_username))


def get_device_grpc_port():
    return int(
        os.environ.get(const.device_gnmi_port, _settings.get(const.device_gnmi_port))
    )


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


def is_grpc_device_listening(host, max_retries=1, interval=1):
    retry = 0
    status = False
    port = get_device_grpc_port()
    while retry < max_retries:
        # Create a TCP socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(get_ping_timeout())
            sock.connect((host, port))
            status = True
            break
        except socket.error as e:
            _logger.error("Failed to connect to %s on port %s: %s", host, port, e)
            retry += 1
            status = False
            time.sleep(interval)  # Wait before retrying
        finally:
            sock.close()
    return status


def validate_and_get_ip_prefix(network_address: str):
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
            ip_network.prefixlen,
        )
    except ValueError:
        _logger.error(f"Invalid network address: {network_address}")
        return None, None, None


def format_and_get_trunk_vlans(trunk_vlans: list):
    """
    Formats and returns the list of trunk VLANs.

    Args:
        trunk_vlans (list): The list of trunk VLANs to format.

    Returns:
        list: The formatted list of trunk VLANs.
    """

    result = []
    for i in trunk_vlans:
        if isinstance(i, int):
            result.append(i)
        elif "-" in i:
            result.extend(
                range(int(i.split("-")[0]), int(i.split("-")[1]) + 1)
            )
        elif ".." in i:
            result.extend(range(int(i.split("..")[0]), int(i.split("..")[1]) + 1))
        else:
            result.append(int(i))
    return result


def get_if_alias(if_alias):
    if "eth" in if_alias.lower():
        if_alias = if_alias.lower().replace("eth", "")
    if_alias_split = if_alias.split("/")
    return f"{if_alias_split[0]}/{if_alias_split[1]}"


def get_number_of_breakouts_and_speed(breakout_mode: str):
    breakout_mode_split = breakout_mode.split("x")
    return int(breakout_mode_split[0]), breakout_mode_split[1]

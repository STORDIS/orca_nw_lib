import ipaddress
import re

import paramiko
from orca_nw_lib.device_gnmi import get_device_details_from_device

from orca_nw_lib.discovery import trigger_discovery
from orca_nw_lib.gnmi_util import remove_stub

from orca_nw_lib.utils import (
    get_device_username,
    get_device_password,
    get_logging,
    is_grpc_device_listening, get_ping_timeout,
)

_logger = get_logging().getLogger(__name__)


def create_ssh_client(
        device_ip: str, username: str, password: str = None
) -> paramiko.SSHClient:
    """
    Creates an SSH client for a device.
    Args:
        device_ip (str): The IP address of the device.
        username (str): The username to use for authentication.
        password (str, optional): The password to use for authentication. Defaults to None.

    Returns:
        paramiko.SSHClient: The SSH client.
    """
    _logger.info("Creating SSH client for device %s", device_ip)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        params = {
            "hostname": device_ip,
            "timeout": get_ping_timeout(),
        }

        if password:
            params["username"] = username
            params["password"] = password
        else:
            params["auth_strategy"] = paramiko.auth_strategy.NoneAuth(username="root")
        ssh.connect(**params)
        return ssh
    except Exception as e:
        _logger.error("Failed to create SSH client for device %s: %s", device_ip, e)
        raise


def run_sonic_cli_command(device_ip: str, command: str) -> tuple[str, str]:
    """
    Runs a command on a device and returns the output.
    Args:
        device_ip (str): The IP address of the device.
        command (str): The command to run on the device.

    Returns:
        str: The output of the command.
    """
    try:
        _logger.debug("Running command %s on device %s", command, device_ip)
        ssh = create_ssh_client(device_ip, get_device_username(), get_device_password())

        stdin, stdout, stderr = ssh.exec_command(command)
        error = stderr.read().decode("utf-8")
        output = stdout.read().decode("utf-8")
        ssh.close()
        return output, error
    except Exception as e:
        return "", str(e)


def run_onie_cli_command(device_ip: str, command: str) -> tuple[str, str]:
    """
    Runs a command on a device and returns the output.
    Args:
        device_ip (str): The IP address of the device.
        command (str): The command to run on the device.

    Returns:
        str: The output of the command.
    """
    try:
        ssh = create_ssh_client(device_ip, "root")
        stdin, stdout, stderr = ssh.exec_command(command)
        error = stderr.read().decode("utf-8")
        output = stdout.read().decode("utf-8")
        ssh.close()
        return output, error
    except Exception as e:
        return "", str(e)


def validate_and_get_onie_details_from_device(device_ip: str) -> tuple[bool, dict or str]:
    """
    Validates and gets ONIE details from a device.
    Args:
        device_ip (str): The IP address of the device.

    Returns:
        tuple[bool, dict or str]: A tuple containing a boolean indicating if ONIE details were found and a dictionary containing the ONIE details or an error message.
    """
    try:
        command = "onie-syseeprom || echo 'ONIE not found'"
        _logger.info("validating onie on %s", device_ip)
        output, error = run_onie_cli_command(device_ip, command)
        if error:
            return False, error
        if "ONIE not found" in output:
            return False, ""
        return True, {**parse_onie_info(output), "mgt_ip": device_ip}
    except Exception as e:
        return False, str(e)


def validate_and_get_sonic_details_from_device(device_ip: str) -> tuple[bool, dict or str]:
    """
    Validates and gets SONiC details from a device.
    Args:
        device_ip (str): The IP address of the device.

    Returns:
        tuple[bool, dict or str]: A tuple containing a boolean indicating if SONiC details were found and a dictionary containing the SONiC details or an error message.
    """
    try:
        _logger.info("validating sonic on %s", device_ip)
        if is_grpc_device_listening(device_ip):
            _logger.info("Getting device details from %s", device_ip)
            details = get_device_details_from_device(device_ip)
            return True, details
        return False, "SONiC not found"
    except Exception as e:
        _logger.error("Failed to get device details from %s: %s", device_ip, e)
        return False, str(e)
    finally:
        remove_stub(device_ip=device_ip)


def install_image_on_device(
        device_ip: str,
        image_url: str,
        discover_also: bool = False,
        username: str = None,
        password: str = None,
):
    """
    Installs an image on a device.
    Args:
        device_ip (str): The IP address of the device.
        image_url (str): The URL of the image to install.
        discover_also (bool, optional): Whether to discover the device. Defaults to False.
        username (str, optional): The username to use for authentication. Defaults to None.
        password (str, optional): The password to use for authentication. Defaults to None.
    """
    try:
        output, error = _install_image(device_ip, image_url, username, password)

        # Rebooting the device after installing the image
        reboot_device(device_ip)

        # Wait for the device to reconnect
        is_grpc_device_listening(device_ip, max_retries=10, interval=10)

        # Trigger discovery if discover_also is True
        if discover_also:
            _logger.info("Triggering discovery on %s", device_ip)
            trigger_discovery(device_ip)
        return {"output": output, "error": error}
    except Exception as e:
        _logger.error("Failed to install image on device %s: %s", device_ip, e)
        return {"output": "", "error": str(e)}


def scan_networks(network_ip: str) -> tuple[list, list]:
    """
    Scans networks on a list of devices.
    Args:
        network_ip (str): The IP address of the network.
    Returns:
        tuple[list, list]: A tuple containing a list of ONIE devices and a list of SONiC devices.
    """
    onie_devices = []
    sonic_devices = []
    network = ipaddress.ip_network(network_ip, strict=False)
    try:
        for ip in network:
            device_ip = str(ip)
            _logger.info("Scanning device %s", device_ip)
            if (result := validate_and_get_onie_details_from_device(device_ip=device_ip))[0]:
                onie_devices.append(result[1])
            elif (result := validate_and_get_sonic_details_from_device(device_ip=device_ip))[0]:
                sonic_devices.append(result[1])
        return onie_devices, sonic_devices
    except Exception as e:
        _logger.error("Failed to scan networks: %s", e)
        return onie_devices, sonic_devices


def _install_image(
        device_ip: str, image_url: str, username: str = None, password: str = None
):
    """
    Installs an image on a device.
    Args:
        device_ip (str): The IP address of the device.
        image_url (str): The URL of the image to install.
        username (str, optional): The username to use for authentication. Defaults to None.
        password (str, optional): The password to use for authentication. Defaults to None.
    """
    image_url_with_credentials = create_url_with_credentials(
        image_url, username, password
    )
    _logger.info("Checking device type on %s", device_ip)
    if validate_and_get_onie_details_from_device(device_ip)[0]:
        return install_image_on_onie_device(device_ip, image_url_with_credentials)
    else:
        return install_image_on_sonic_device(device_ip, image_url_with_credentials)


def install_image_on_onie_device(device_ip: str, image_url: str):
    """
    Installs an image on an ONIE device.
    Args:
        device_ip (str): The IP address of the ONIE device.
        image_url (str): The URL of the image to install.
    """
    _logger.info("Installing image on ONIE device %s", device_ip)
    command = f'/bin/sh -l -c "onie-nos-install {image_url}"'
    output, error = run_onie_cli_command(device_ip, command)
    return output, error


def install_image_on_sonic_device(device_ip: str, image_url: str):
    """
    Installs an image on a SONiC device.
    Args:
        device_ip (str): The IP address of the SONiC device.
        image_url (str): The URL of the image to install.
    """
    _logger.info("Installing image on SONiC device %s", device_ip)
    command = f"sudo sonic-installer install {image_url} -y"
    output, error = run_sonic_cli_command(device_ip, command)
    return output, error


def get_onie_device_details(device_ip: str):
    """
    Retrieves the details of a device based on its IP address.
    Args:
        device_ip (str): The IP address of the device.
    """
    result = {}
    _logger.info("Getting ONIE details of device %s", device_ip)
    output, error = run_onie_cli_command(device_ip, "onie-syseeprom")
    if not error:
        result = parse_onie_info(output)
    result["mgt_ip"] = device_ip
    return result


def switch_image_on_device(device_ip: str, image_name: str):
    """
    Switches the image on a device.
    Args:
        device_ip (str): The IP address of the device.
        image_name (str): The name of the image to switch to.
    """
    try:
        _logger.info("Switching image on device %s.", device_ip)
        cmd = f"sudo sonic-installer set-default {image_name}"
        output, error = run_sonic_cli_command(device_ip, cmd)
        if error:
            _logger.error("Error: %s", error)
        else:
            _logger.info("Successfully changed image on device %s.", device_ip)

        # Rebooting the device to apply the change
        run_sonic_cli_command(device_ip, "sudo reboot")
        # Wait for the device to reconnect
        status = is_grpc_device_listening(device_ip, max_retries=10, interval=10)
        if status:
            # Trigger discovery if discover_also is True
            try:
                _logger.info("Triggering discovery on device %s.", device_ip)
                trigger_discovery(device_ip)
            except Exception as e:
                _logger.error(
                    "Failed to trigger discovery on device %s. Error: %s", device_ip, e
                )
        return output, error
    except Exception as e:
        _logger.error("Failed to change image on device %s. Error: %s", device_ip, e)


def reboot_device(device_ip: str):
    """
    Reboots a device.
    Args:
        device_ip (str): The IP address of the device.
    """
    try:
        _logger.info("Rebooting device %s.", device_ip)
        return run_sonic_cli_command(device_ip, "sudo reboot")
    except Exception as e:
        _logger.error("Failed to reboot device %s. Error: %s", device_ip, e)


def create_url_with_credentials(base_url, username: str = None, password: str = None):
    """
    Function to generate a URL with embedded username and password.

    Parameters:
        base_url (str): The base URL without credentials (e.g., "https://example.com").
        username (str): The username to embed in the URL.
        password (str): The password to embed in the URL.

    Returns:
        str: The URL with embedded username and password.
    """

    if username and password:
        # Extract the scheme (http/https) and the rest of the URL
        scheme, url_without_scheme = base_url.split("://")
        # Embed the username and password into the URL
        url_with_credentials = f"{scheme}://{username}:{password}@{url_without_scheme}"
        return url_with_credentials
    else:
        return base_url


def parse_onie_info(output: str) -> dict:
    """
    Function to parse the output of the onie-syseeprom command.

    Args:
        output (str): The output of the onie-nos-install command.

    Returns:
        dict: A dictionary containing the parsed output.
    """
    parsed_data = {}

    # Regex pattern to match each TLV entry
    pattern = re.compile(r'(.+?)\s+0x([0-9A-F]+)\s+\d+\s+(.+)')

    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            name, _, value = match.groups()
            parsed_data[name.strip()] = value.strip()
    return parsed_data

import ipaddress
import time

import paramiko
from orca_nw_lib.device import discover_device

from orca_nw_lib.discovery import trigger_discovery
from paramiko.auth_strategy import AuthStrategy

from orca_nw_lib.utils import get_device_username, get_device_password, get_logging, is_grpc_device_listening

_logger = get_logging().getLogger(__name__)


def create_ssh_client(device_ip: str, username: str, password: str = None) -> paramiko.SSHClient:
    """
    Creates an SSH client for a device.
    Args:
        device_ip (str): The IP address of the device.
        username (str): The username to use for authentication.
        password (str, optional): The password to use for authentication. Defaults to None.

    Returns:
        paramiko.SSHClient: The SSH client.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    params = {
        "hostname": device_ip,
        "timeout": 5,
    }

    if password:
        params["username"] = username
        params["password"] = password
    else:
        params["auth_strategy"] = paramiko.auth_strategy.NoneAuth(
            username="root"
        )
    ssh.connect(**params)
    return ssh


def run_sonic_cli_command(device_ip: str, command: str) -> str:
    """
    Runs a command on a device and returns the output.
    Args:
        device_ip (str): The IP address of the device.
        command (str): The command to run on the device.

    Returns:
        str: The output of the command.
    """
    ssh = create_ssh_client(device_ip, get_device_username(), get_device_password())

    stdin, stdout, stderr = ssh.exec_command(command)
    error = stderr.read().decode("utf-8")
    output = stdout.read().decode("utf-8")
    ssh.close()
    return output, error


def run_onie_cli_command(device_ip: str, command: str) -> str:
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


def check_onie_on_device(device_ip: str) -> bool:
    """
    Checks if ONIE is installed on a device.
    Args:
        device_ip (str): The IP address of the device.

    Returns:
        bool: True if ONIE is installed, False otherwise.
    """
    command = "onie-sysinfo || echo 'ONIE not found'"
    output, error = run_onie_cli_command(device_ip, command)
    if error:
        return False
    if "ONIE not found" in output:
        return False
    return True


def install_image_on_device(device_ip: str, image_url: str, discover_also: bool = False):
    """
    Installs an image on a device.
    Args:
        device_ip (str): The IP address of the device.
        image_url (str): The URL of the image to install.
        discover_also (bool, optional): Whether to discover the device. Defaults to False.
    """
    try:
        if "/" in device_ip:
            network = ipaddress.ip_network(device_ip, strict=False)
            return [
                get_onie_device_details(str(ip)) for ip in network if check_onie_on_device(str(ip))
            ]
        else:
            output, error = _install_image(device_ip, image_url)

            # Rebooting the device after installing the image
            reboot_device(device_ip)

            # Wait for the device to reconnect
            is_grpc_device_listening(device_ip, max_retries=10, interval=10)

            # Trigger discovery if discover_also is True
            if discover_also:
                trigger_discovery(device_ip)
            return {"output": output, "error": error}
    except Exception as e:
        return {"output": "", "error": str(e)}


def _install_image(device_ip: str, image_url: str):
    """
    Installs an image on a device.
    Args:
        device_ip (str): The IP address of the device.
        image_url (str): The URL of the image to install.
    """
    if check_onie_on_device(device_ip):
        return install_image_on_onie_device(device_ip, image_url)
    else:
        return install_image_on_sonic_device(device_ip, image_url)


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

    # Rebooting the device after installing the image
    reboot_device(device_ip)
    return output, error


def get_onie_device_details(device_ip: str):
    """
    Retrieves the details of a device based on its IP address.
    Args:
        device_ip (str): The IP address of the device.
    """
    details = {
        "ip": device_ip
    }
    output, error = run_onie_cli_command(device_ip, "onie-sysinfo -e")
    if not error:
        details["mac_address"] = output.replace("\n", "")
    output, error = run_onie_cli_command(device_ip, "onie-sysinfo -p")
    if not error:
        details["platform"] = output.replace("\n", "")
    output, error = run_onie_cli_command(device_ip, "onie-sysinfo -v")
    if not error:
        details["version"] = output.replace("\n", "")
    return details


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

from prometheus_client import CollectorRegistry, Info
from orca_nw_lib.promdb_utils import write_to_prometheus

def insert_device_info_in_prometheus(device_info):
    """
    Converts the Device object into Prometheus metrics and pushes them to the Pushgateway.
    
    Args:
        device_info (Device): The Device object containing device details.
    """
    try:
        # Create a registry for this device
        registry = CollectorRegistry()

        # Define an Info metric for device details
        info_device_details = Info(
            'device_details',
            'Detailed information about the device',
            registry=registry
        )

        # Extract relevant data
        device_name = device_info.img_name  # Use image name or another identifier as the label

        # if device_info.system_status == "System is ready":
        #     system_status_int = 1
        # else:
        #     system_status_int = 0
        system_status_int = 1 if device_info.system_status == "System is ready" else 0

        # Update the Info metric with other descriptive details
        info_device_details.info({
            "device_name": device_name,
            "image_name": device_info.img_name,
            "management_interface": device_info.mgt_intf,
            "management_ip": device_info.mgt_ip,
            "hardware_sku": device_info.hwsku,
            "mac_address": device_info.mac,
            "platform": device_info.platform,
            "device_type": device_info.type,
            "system_status": str(system_status_int) # Keep this as a string description
        })

        # Push metrics to the Pushgateway
        write_to_prometheus(registry=registry)

        print(f"Metrics successfully pushed to Pushgateway for device: {device_name}")

    except Exception as e:
        print(f"Failed to push metrics to Pushgateway for device {device_info.img_name}: {e}")

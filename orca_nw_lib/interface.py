import datetime
from typing import Dict, List

import pytz

from orca_nw_lib.common import Speed, getSpeedStrFromOCStr
from orca_nw_lib.device_db import get_device_db_obj
from orca_nw_lib.graph_db_models import Interface, SubInterface
from orca_nw_lib.interface_db import (
    get_all_interfaces_of_device_from_db,
    get_interface_of_device_from_db,
    insert_device_interfaces_in_db,
)
from orca_nw_lib.interface_gnmi import (
    del_all_subinterfaces_of_interface_from_device,
    get_all_interfaces_from_device,
    set_interface_config_on_device,
)
from orca_nw_lib.utils import get_logging


_logger = get_logging().getLogger(__name__)


def create_interface_graph_objects(device_ip: str) -> List[Interface]:
    interfaces_json = get_all_interfaces_from_device(device_ip)
    intfc_graph_obj_list: Dict[Interface, List[SubInterface]] = {}
    for intfc in interfaces_json.get("openconfig-interfaces:interface") or []:
        intfc_state = intfc.get("state", {})
        intfc_counters = intfc_state.get("counters", {})
        type = intfc.get("config").get("type")

        if (
            "ether" or "loopback" in type.lower()
        ) and "PortChannel" not in intfc_state.get("name"):
            # Port channels are separately discovered so skip them in interface discovery
            interface = Interface(
                name=intfc_state.get("name"),
                enabled=intfc_state.get("enabled"),
                mtu=intfc_state.get("mtu"),
                fec=intfc.get("openconfig-if-ethernet:ethernet", {})
                .get("config", {})
                .get("openconfig-if-ethernet-ext2:port-fec"),
                speed=getSpeedStrFromOCStr(s)
                if (
                    s := intfc.get("openconfig-if-ethernet:ethernet", {})
                    .get("config", {})
                    .get("port-speed")
                )
                else None,
                oper_sts=intfc_state.get("oper-status"),
                admin_sts=intfc_state.get("admin-status"),
                description=intfc_state.get("description"),
                last_chng=(
                    (lambda utc_date: f"{str(utc_date)} {utc_date.tzinfo}")(
                        datetime.datetime.utcfromtimestamp(int(last_chng)).replace(
                            tzinfo=pytz.utc
                        )
                        if (last_chng := 1688989316)
                        else 0
                    )
                ),
                mac_addr=intfc_state.get("mac-address"),
                in_bits_per_second=intfc_counters.get("in-bits-per-second"),
                in_broadcast_pkts=intfc_counters.get("in-broadcast-pkts"),
                in_discards=intfc_counters.get("in-discards"),
                in_errors=intfc_counters.get("in-errors"),
                in_multicast_pkts=intfc_counters.get("in-multicast-pkts"),
                in_octets=intfc_counters.get("in-octets"),
                in_octets_per_second=intfc_counters.get("in-octets-per-second"),
                in_pkts=intfc_counters.get("in-pkts"),
                in_pkts_per_second=intfc_counters.get("in-pkts-per-second"),
                in_unicast_pkts=intfc_counters.get("in-unicast-pkts"),
                in_utilization=intfc_counters.get("in-utilization"),
                last_clear=intfc_counters.get("last-clear"),
                out_bits_per_second=intfc_counters.get("out-bits-per-second"),
                out_broadcast_pkts=intfc_counters.get("out-broadcast-pkts"),
                out_discards=intfc_counters.get("out-discards"),
                out_errors=intfc_counters.get("out-errors"),
                out_multicast_pkts=intfc_counters.get("out-multicast-pkts"),
                out_octets=intfc_counters.get("out-octets"),
                out_octets_per_second=intfc_counters.get("out-octets-per-second"),
                out_pkts=intfc_counters.get("out-pkts"),
                out_pkts_per_second=intfc_counters.get("out-pkts-per-second"),
                out_unicast_pkts=intfc_counters.get("out-unicast-pkts"),
                out_utilization=intfc_counters.get("out-utilization"),
            )
            sub_intf_obj_list = []
            for sub_intfc in intfc.get("subinterfaces", {}).get("subinterface", {}):
                sub_intf_obj = SubInterface()
                for addr in (
                    sub_intfc.get("openconfig-if-ip:ipv4", {})
                    .get("addresses", {})
                    .get("address")
                    or []
                ):
                    if addr.get("ip"):
                        sub_intf_obj.ip_address = addr.get("ip")
                    sub_intf_obj_list.append(sub_intf_obj)

            intfc_graph_obj_list[interface] = sub_intf_obj_list
        elif "lag" in type.lower():
            # its a port channel
            pass
        else:
            _logger.error(f"Unknown Interface type {type}")

    return intfc_graph_obj_list


def get_possible_speeds():
    return [str(e) for e in Speed]


def get_interface(device_ip: str, intfc_name=None) -> List[dict]:
    """
    Get the interface information of a device from DB in JSON format.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str, optional): The name of the interface. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries containing the properties of the interfaces stored in the DB.



    """
    op_dict: List[dict] = []

    if intfc_name:
        intfc = get_interface_of_device_from_db(device_ip, intfc_name)
        if intfc:
            op_dict.append(intfc.__properties__)
    else:
        interfaces = get_all_interfaces_of_device_from_db(device_ip)
        for intfc in interfaces or []:
            op_dict.append(intfc.__properties__)
    return op_dict


def config_interface(device_ip: str, intfc_name: str, **kwargs):
    """
    Configure the interface of a device.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.
        kwargs (dict): The configuration parameters of the interface.

    kwargs:
        enable (bool, optional): The enable status of the interface. Defaults to None.
        loopback (bool, optional): The loopback status of the interface. Defaults to None.
        mtu (int, optional): The maximum transmission unit of the interface. Defaults to None.
        speed (Speed, optional): The speed of the interface. Defaults to None.
        description (str, optional): The description of the interface. Defaults to None.
        ip (str, optional): The IP address of the interface. Defaults to None.
        ip_prefix_len (int, optional): The IP prefix length of the interface. Defaults to 0.
        index (int, optional): The index of the sub-interface. Defaults to 0.

    """
    _logger.debug(f"Configuring interface {intfc_name} on device {device_ip}")
    set_interface_config_on_device(device_ip, intfc_name, **kwargs)
    discover_interfaces(device_ip)
    _logger.debug(f"Configured interface {intfc_name} on device {device_ip}")


def del_ip_from_intf(device_ip: str, intfc_name: str):
    """
    Delete an IP address from an interface.

    Parameters:
        device_ip (str): The IP address of the device.
        intfc_name (str): The name of the interface.

    """
    del_all_subinterfaces_of_interface_from_device(device_ip, intfc_name)


def discover_interfaces(device_ip: str = None):
    _logger.info("Interface Discovery Started.")
    devices = [get_device_db_obj(device_ip)] if device_ip else get_device_db_obj()
    for device in devices:
        _logger.info(f"Discovering interfaces of device {device}.")
        insert_device_interfaces_in_db(
            device, create_interface_graph_objects(device.mgt_ip)
        )

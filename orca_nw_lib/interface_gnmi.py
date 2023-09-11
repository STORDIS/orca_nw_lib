from orca_nw_lib.common import Speed
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db
from orca_nw_lib.gnmi_util import create_gnmi_update, create_req_for_update, get_gnmi_del_req, send_gnmi_get, send_gnmi_set
import orca_nw_lib.portgroup_db
import orca_nw_lib.portgroup_gnmi


def get_interface_base_path():
    return Path(
        target="openconfig",
        elem=[
            PathElem(
                name="openconfig-interfaces:interfaces",
            )
        ],
    )


def get_interface_path(intfc_name: str):
    path = get_interface_base_path()
    path.elem.append(PathElem(name="interface", key={"name": intfc_name}))
    return path


def get_sub_interface_base_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="subinterfaces"))
    return path


def get_sub_interface_path(intfc_name: str):
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface"))
    return path


def get_sub_interface_index_path(intfc_name: str, index: int):
    path = get_sub_interface_base_path(intfc_name)
    path.elem.append(PathElem(name="subinterface", key={"index": str(index)}))
    return path


def get_all_interfaces_path():
    path = get_interface_base_path()
    path.elem.append(PathElem(name="interface"))
    return path


def get_intfc_config_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="config"))
    return path


def get_intfc_speed_path(intfc_name: str):
    path = get_interface_path(intfc_name)
    path.elem.append(PathElem(name="openconfig-if-ethernet:ethernet"))
    path.elem.append(PathElem(name="config"))
    path.elem.append(PathElem(name="port-speed"))
    return path


def get_intfc_enabled_path(intfc_name: str):
    path = get_intfc_config_path(intfc_name)
    path.elem.append(PathElem(name="enabled"))
    return path


def set_interface_config_on_device(
    device_ip: str,
    interface_name: str,
    enable: bool = None,
    mtu: int = None,
    loopback: bool = None,
    description: str = None,
    speed: Speed = None,
    ip: str = None,
    ip_prefix_len: int = 0,
    index: int = 0,
):
    updates = []

    if enable is not None:
        updates.append(
            create_gnmi_update(
                get_intfc_enabled_path(interface_name),
                {"openconfig-interfaces:enabled": enable},
            )
        )

    if mtu is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="mtu"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:mtu": mtu},
            )
        )

    if loopback is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="loopback-mode"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:loopback-mode": loopback},
            )
        )

    if description is not None:
        base_config_path = get_intfc_config_path(interface_name)
        base_config_path.elem.append(PathElem(name="description"))
        updates.append(
            create_gnmi_update(
                base_config_path,
                {"openconfig-interfaces:description": description},
            )
        )

    if speed is not None:
        # if switch supports port groups then configure speed on port-group otherwise directly on interface
        if orca_nw_lib.portgroup_db.get_all_port_groups_of_device_from_db(
            device_ip
        ) and orca_nw_lib.portgroup_db.get_port_group_id_of_device_interface_from_db(device_ip, interface_name):
            pg_id = orca_nw_lib.portgroup_db.get_port_group_id_of_device_interface_from_db(device_ip, interface_name)
            updates.append(
                create_gnmi_update(
                    orca_nw_lib.portgroup_gnmi._get_port_group_speed_path(pg_id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            )

        else:
            updates.append(
                create_gnmi_update(
                    get_intfc_speed_path(interface_name),
                    {"port-speed": speed.get_oc_val()},
                )
            )

    if ip is not None:
        ip_payload = {
            "openconfig-interfaces:subinterface": [
                {
                    "config": {"index": index},
                    "index": index,
                    "openconfig-if-ip:ipv4": {
                        "addresses": {
                            "address": [
                                {
                                    "ip": ip,
                                    "config": {
                                        "prefix-length": ip_prefix_len,
                                        "secondary": False,
                                    },
                                }
                            ]
                        }
                    },
                }
            ]
        }
        updates.append(
            create_gnmi_update(
                get_sub_interface_path(interface_name),
                ip_payload,
            )
        )

    if updates:
        return send_gnmi_set(
            create_req_for_update(updates),
            device_ip,
        )
    else:
        return None


def get_all_interfaces_from_device(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_all_interfaces_path()])


def get_interface_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_interface_path(intfc_name)])


def get_interface_config_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_config_path(intfc_name)])


def get_interface_speed_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_speed_path(intfc_name)])


def get_interface_status_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_intfc_enabled_path(intfc_name)])


def get_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(if_name)])


def del_all_subinterfaces_of_interface_from_device(device_ip: str, if_name: str):
    return send_gnmi_set(get_gnmi_del_req(get_sub_interface_path(if_name)), device_ip)


def del_all_subinterfaces_of_all_interfaces_from_device(device_ip: str):
    for ether in get_all_interfaces_name_of_device_from_db(device_ip):
        del_all_subinterfaces_of_interface_from_device(device_ip, ether)


def del_subinterface_of_interface_from_device(device_ip: str, if_name: str, index: int):
    return send_gnmi_set(
        get_gnmi_del_req(get_sub_interface_index_path(if_name, index)), device_ip
    )


def get_subinterface_from_device(device_ip: str, if_name: str, index: int):
    return send_gnmi_get(
        device_ip=device_ip, path=[get_sub_interface_index_path(if_name, index)]
    )


def get_all_subinterfaces_from_device(device_ip: str, intfc_name: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_sub_interface_path(intfc_name)])
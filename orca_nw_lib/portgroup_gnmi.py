from orca_nw_lib.common import Speed
from orca_nw_lib.gnmi_pb2 import Path, PathElem
from orca_nw_lib.gnmi_util import create_gnmi_update, create_req_for_update, send_gnmi_get, send_gnmi_set


def _get_port_groups_base_path():
    return Path(
        target="openconfig",
        origin="openconfig-port-group",
        elem=[
            PathElem(
                name="port-groups",
            ),
        ],
    )


def _get_port_groups_path():
    path = _get_port_groups_base_path()
    path.elem.append(
        PathElem(
            name="port-group",
        )
    )
    return path


def _get_port_group_path(id: str):
    path = _get_port_groups_base_path()
    path.elem.append(PathElem(name="port-group", key={"id": str(id)}))
    return path


def _get_port_group_config_path(id: str):
    path = _get_port_group_path(id)
    path.elem.append(PathElem(name="config"))
    return path


def _get_port_group_speed_path(id: str):
    path = _get_port_group_config_path(id)
    path.elem.append(PathElem(name="speed"))
    return path


def get_port_chnl_mem_base_path():
    return Path(
        target="openconfig",
        origin="sonic-portchannel",
        elem=[PathElem(name="sonic-portchannel"), PathElem(name="PORTCHANNEL_MEMBER")],
    )


def get_port_groups(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_groups_path()])


def get_port_group(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_group_path(id)])


def get_port_group_speed(device_ip: str, id: int):
    return send_gnmi_get(device_ip=device_ip, path=[_get_port_group_speed_path(id)])


def set_port_group_speed(device_ip: str, id: int, speed: Speed):
    return send_gnmi_set(
        create_req_for_update(
            [
                create_gnmi_update(
                    _get_port_group_speed_path(id),
                    {"openconfig-port-group:speed": speed.get_oc_val()},
                )
            ]
        ),
        device_ip,
    )
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import send_gnmi_set, get_gnmi_update_req


def enable_interface(device_ip: str, interface_name: str, enable: bool):
    path_intf_status_path = Path(target='openconfig',
                                 origin='openconfig-interfaces',
                                 elem=[PathElem(name="interfaces", ),
                                       PathElem(name="interface", key={
                                                "name": interface_name}),
                                       PathElem(name="config"),
                                       PathElem(name="enabled"),
                                       ])
    return send_gnmi_set(get_gnmi_update_req(path_intf_status_path, 
                                             {"openconfig-interfaces:enabled": enable}), device_ip)

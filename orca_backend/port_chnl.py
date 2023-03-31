from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import get_gnmi_del_req, get_gnmi_update_req, send_gnmi_get, send_gnmi_set


def add_port_chnl(device_ip: str, chnl_name: str):
    path = Path(target='openconfig',
                origin='sonic-portchannel',
                elem=[PathElem(name="sonic-portchannel"),
                      PathElem(name="PORTCHANNEL"),
                      PathElem(name="PORTCHANNEL_LIST"),
                      ])
    port_chnl_add = {
        "sonic-portchannel:PORTCHANNEL_LIST": []
    }
    port_chnl_add.get(
        "sonic-portchannel:PORTCHANNEL_LIST").append({"name": chnl_name})
    return send_gnmi_set(get_gnmi_update_req(path, port_chnl_add), device_ip)



def add_port_chnl_member(device_ip: str, chnl_name: str, ifname:str):
    path = Path(target='openconfig',
                origin='sonic-portchannel',
                elem=[PathElem(name="sonic-portchannel"),
                      PathElem(name="PORTCHANNEL_MEMBER"),
                      PathElem(name="PORTCHANNEL_MEMBER_LIST"),
                      ])
    port_chnl_add = {
        "sonic-portchannel:PORTCHANNEL_MEMBER_LIST": []
    }
    port_chnl_add.get(
        "sonic-portchannel:PORTCHANNEL_MEMBER_LIST").append({"name": chnl_name,"ifname":ifname})
    return send_gnmi_set(get_gnmi_update_req(path, port_chnl_add), device_ip)




def remove_port_chnl_member(device_ip: str, chnl_name: str, ifname:str):
    path = Path(target='openconfig',
                origin='sonic-portchannel',
                elem=[PathElem(name="sonic-portchannel"),
                      PathElem(name="PORTCHANNEL_MEMBER"),
                      PathElem(name="PORTCHANNEL_MEMBER_LIST",
                               key={"name": chnl_name,"ifname": ifname}),
                      ])
    return send_gnmi_set(get_gnmi_del_req(path), device_ip)



def del_port_chnl(device_ip: str, chnl_name: str):
    path = Path(target='openconfig',
                origin='sonic-portchannel',
                elem=[PathElem(name="sonic-portchannel"),
                      PathElem(name="PORTCHANNEL"),
                      PathElem(name="PORTCHANNEL_LIST",
                               key={"name": chnl_name}),
                      ])
    return send_gnmi_set(get_gnmi_del_req(path), device_ip)


def get_port_chnl(device_ip: str):
    path_intf_status_path = Path(target='openconfig',
                                 origin='sonic-portchannel',
                                 elem=[PathElem(name="sonic-portchannel"),
                                       ])
    return send_gnmi_get(device_ip, [path_intf_status_path])


def del_all_port_chnl(device_ip: str):
    path = Path(target='openconfig',
                origin='sonic-portchannel',
                elem=[PathElem(name="sonic-portchannel"),
                      PathElem(name="PORTCHANNEL"),
                      PathElem(name="PORTCHANNEL_LIST"),
                      ])
    return send_gnmi_set(get_gnmi_del_req(path), device_ip)

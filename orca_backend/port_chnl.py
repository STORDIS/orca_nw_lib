import json
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import get_gnmi_del_req, get_gnmi_update_req, send_gnmi_get, send_gnmi_set
from orca_backend.graph_db_models import PortChannel
from orca_backend.graph_db_utils import getAllPortChnlOfDevice


def createPortChnlGraphObject(device_ip: str):
    port_chnl_json = get_port_chnl(device_ip)
    port_chnl_obj_list = {}
    if port_chnl_json:
        lag_table_json_list = port_chnl_json.get(
            'sonic-portchannel:sonic-portchannel').get('LAG_TABLE',{}).get('LAG_TABLE_LIST')
        lag_mem_table_json_list = port_chnl_json.get(
            'sonic-portchannel:sonic-portchannel').get('LAG_MEMBER_TABLE',{}).get('LAG_MEMBER_TABLE_LIST')
        for lag in lag_table_json_list:
            ifname_list=[]
            for mem in lag_mem_table_json_list:
                if lag.get('lagname') == mem.get('name'):
                    ifname_list.append(mem.get('ifname'))
            port_chnl_obj_list[PortChannel(active=lag.get('active'),
                                            lag_name=lag.get('lagname'),
                                            admin_sts=lag.get('admin_status'),
                                            mtu=lag.get('mtu'),
                                            name=lag.get('name'),
                                            fallback_operational=lag.get(
                                                'fallback_operational'),
                                            oper_sts=lag.get('oper_status'),
                                            speed=lag.get('speed'),
                                            oper_sts_reason=lag.get('reason'),
                                            )]=ifname_list
    return port_chnl_obj_list


def getPortChnlDetailsFromGraph(device_ip:str):
    port_chnl=getAllPortChnlOfDevice(device_ip)
    op_dict = []
    for chnl in port_chnl or []:
        op_dict.append(chnl.__properties__)
    return op_dict


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

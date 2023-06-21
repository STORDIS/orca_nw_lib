
from .gnmi_pb2 import Path, PathElem
from .gnmi_util import (
    create_req_for_update,
    send_gnmi_set,
    create_gnmi_update,
    send_gnmi_get,
)
from .graph_db_models import PortGroup
from .graph_db_utils import getAllInterfacesOfDevice, getInterfaceOfDevice
from .utils import get_logging
from .common import Speed

_logger = get_logging().getLogger(__name__)


def getLLDPNeighbors(device_ip: str):
    lldp_json = get_lldp_interfaces(device_ip)
    neighbors=[]
    for intfs in lldp_json.get("openconfig-lldp:interface") or []:
        local_port_name=intfs.get('name')
        if intfs.get("neighbors") or []:
            if not intfs.get("neighbors").get("neighbor"):
                _logger.error(f"Can't find neighbor in {device_ip}:{intfs.get('name')}")

            for nbr in intfs.get("neighbors").get("neighbor") or []:
                nbr_addr = nbr.get("state").get("management-address")
                if not nbr_addr:
                    _logger.error(f"can find neighbor addr in {nbr}")
                nbr_port = nbr.get("state").get("port-id")
                nbr_data={}
                nbr_data['local_port']=local_port_name
                nbr_data['nbr_ip']=nbr_addr.split(",")[0]
                nbr_data['nbr_port']=nbr_port
                neighbors.append(nbr_data)
    return neighbors


def get_lldp_interfaces_path():
    return Path(
            target="openconfig",
            origin="openconfig-lldp",
            elem=[
                PathElem(
                    name="lldp",
                ),
                PathElem(
                    name="interfaces",
                ),
                PathElem(
                    name="interface",
                ),
            ],
        )


def get_lldp_interfaces(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[get_lldp_interfaces_path()])


import json
import re
import ssl
import sys
from typing import List
from grpc._channel import _InactiveRpcError
import grpc
from .gnmi_pb2 import JSON_IETF, GetRequest, Path, SetRequest, TypedValue, Update
from .gnmi_pb2_grpc import gNMIStub

from .utils import get_logging, get_orca_config, ping_ok


from .constants import grpc_port, username, password, conn_timeout

_logger = get_logging().getLogger(__name__)

stubs = {}


def getGrpcStubs(
    device_ip,
    grpc_port=get_orca_config().get(grpc_port),
    username=get_orca_config().get(username),
    password=get_orca_config().get(password),
):
    global stubs

    if not ping_ok(device_ip):
        raise ValueError(f"Device : {device_ip} is not pingable")

    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        try:
            sw_cert = ssl.get_server_certificate(
                (device_ip, grpc_port), timeout=get_orca_config().get(conn_timeout)
            ).encode("utf-8")
            # Option 1
            # creds = grpc.ssl_channel_credentials(root_certificates=sw_cert)
            # stub.Get(GetRequest(path=[path], type=GetRequest.ALL, encoding=JSON_IETF),
            #        metadata=[("username", user),
            #                  ("password", passwd)], )

            # Option 2, In this case need not to send user/pass in metadata in get request.
            def auth_plugin(context, callback):
                callback([("username", username), ("password", password)], None)

            creds = grpc.composite_channel_credentials(
                grpc.ssl_channel_credentials(root_certificates=sw_cert),
                grpc.metadata_call_credentials(auth_plugin),
            )

            optns = (("grpc.ssl_target_name_override", "localhost"),)
            channel = grpc.secure_channel(
                f"{device_ip}:{grpc_port}", creds, options=optns
            )
            stub = gNMIStub(channel)
            stubs[device_ip] = stub
            return stub
        except TimeoutError as te:
            raise te
            # _logger.error(f"Connection Timeout on {device_ip}")
        except ConnectionRefusedError as cr:
            raise cr
            # _logger.error(f"Connection refused by {device_ip}")


def send_gnmi_get(device_ip, path: list[Path]):
    op = {}
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        resp = (
            device_gnmi_stub.Get(
                GetRequest(path=path, type=GetRequest.ALL, encoding=JSON_IETF),
                timeout=get_orca_config().get(conn_timeout),
            )
            if device_gnmi_stub
            else _logger.error(f"no gnmi stub found for device {device_ip}")
        )
        # resp_cap=device_gnmi_stub.Capabilities(CapabilityRequest())
        # print(resp_cap)
        
        for n in resp.notification:
            for u in n.update:
                op.update(json.loads(u.val.json_ietf_val.decode("utf-8")))
        return op
    except _InactiveRpcError as e:
        _logger.debug(
            f"{e} \n on device_ip : {device_ip} \n requested gnmi_path : {path}"
        )
        raise


def create_gnmi_update(path: Path, val: dict):
    return Update(
        path=path, val=TypedValue(json_ietf_val=bytes(json.dumps(val), "utf-8"))
    )


def create_req_for_update(updates: List[Update]):
    return SetRequest(update=updates)


def get_gnmi_del_req(path: Path):
    return SetRequest(delete=[path])


def send_gnmi_set(req: SetRequest, device_ip: str):
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        if device_gnmi_stub:
            device_gnmi_stub.Set(req, timeout=get_orca_config().get(conn_timeout))
        else :
            _logger.error(f"no gnmi stub found for device {device_ip}")
    except _InactiveRpcError as e:
        _logger.debug(
            f"{e} \n on device_ip : {device_ip} \n set request : {req}"
        )
        raise


def create_gnmi_path(path_arr: List[str]) -> List[Path]:
    """Returns a list of gnmi path object create from string formated path array"""
    paths = []
    for path in path_arr:
        gnmi_path = Path()

        path_elements = path.split("/")
        print(path_elements)

        for pe_entry in path_elements:
            if not re.match(".+?:.+?", pe_entry) and len(path_elements) == 1:
                sys.exit(
                    f"You haven't specified either YANG module or the top-level container in '{pe_entry}'."
                )

            elif re.match(".+?:.+?", pe_entry):
                gnmi_path.origin = pe_entry.split(":")[0]
                gnmi_path.elem.add(name=pe_entry.split(":")[1])

            elif re.match(".+?\[.+?\]", pe_entry):
                gnmi_path.elem.add(
                    name=pe_entry.split("[")[0],
                    key={
                        f'{pe_entry.split("[")[1].split("=")[0]}': f'{re.sub("]", "", pe_entry.split("[")[1].split("=")[1])}'
                    },
                )

            else:
                gnmi_path.elem.add(name=pe_entry)
            paths.append(gnmi_path)
    return paths


    
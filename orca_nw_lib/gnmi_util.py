import enum
import json
import re
import ssl
import sys
from typing import List

import grpc
from .gnmi_pb2 import (
    JSON,
    CapabilityRequest,
    Encoding,
    GetRequest,
    Path,
    PathElem,
    JSON_IETF,
    SetRequest,
    SubscribeRequest,
    Subscription,
    SubscriptionList,
    SubscriptionMode,
    TypedValue,
    Update,
)
from .gnmi_pb2_grpc import gNMIStub
from .utils import ping_ok, settings, logging
from .constants import grpc_port, username, password, conn_timeout

_logger = logging.getLogger(__name__)

stubs = {}


def getGrpcStubs(
    device_ip,
    grpc_port=settings.get(grpc_port),
    username=settings.get(username),
    password=settings.get(password),
):
    global stubs

    if not ping_ok(device_ip):
        raise ValueError(f"Device : {device_ip} is not pingable")

    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        try:
            sw_cert = ssl.get_server_certificate(
                (device_ip, grpc_port), timeout=settings.get(conn_timeout)
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
                timeout=settings.get(conn_timeout),
            )
            if device_gnmi_stub
            else _logger.error(f"no gnmi stub found for device {device_ip}")
        )
        # resp_cap=device_gnmi_stub.Capabilities(CapabilityRequest())
        # print(resp_cap)
        for u in resp.notification[0].update:
            op = u.val.json_ietf_val.decode("utf-8")
            op = json.loads(op)
    except Exception as e:
        _logger.error(e)
    return op


def create_gnmi_update(path: Path, val: dict):
    return Update(
        path=path, val=TypedValue(json_ietf_val=bytes(json.dumps(val), "utf-8"))
    )


def create_req_for_update(updates: List[Update]):
    return SetRequest(update=updates)


def get_gnmi_del_req(path: Path):
    return SetRequest(delete=[path])


def send_gnmi_set(req: SetRequest, device_ip: str):
    resp = ""
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        resp = (
            device_gnmi_stub.Set(req, timeout=settings.get(conn_timeout))
            if device_gnmi_stub
            else _logger.error(f"no gnmi stub found for device {device_ip}")
        )
    except Exception as e:
        _logger.error(e)
    return resp


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


def subscribe_to_path(request):
    yield request


def gnmi_subscribe(device_ip: str, paths: List[Path]):
    op = []
    device_gnmi_stub = getGrpcStubs(device_ip)
    try:
        subscriptionlist = SubscriptionList(
            subscription=[
                Subscription(path=path, mode=SubscriptionMode.ON_CHANGE)
                for path in paths
            ],
            mode=SubscriptionList.Mode.Value("STREAM"),
            encoding=Encoding.Value("PROTO"),
        )

        sub_req = SubscribeRequest(subscribe=subscriptionlist)
        for resp in device_gnmi_stub.Subscribe(subscribe_to_path(sub_req)):
            op.append(resp)
    except Exception as e:
        _logger.error(e)
    return op

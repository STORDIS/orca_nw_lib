import json
import ssl
from typing import List
import grpc
from .gnmi_pb2 import (
    JSON_IETF,
    GetRequest,
    Path,
    PathElem,
    SetRequest,
    TypedValue,
    Update,
)
from .gnmi_pb2_grpc import gNMIStub
import ast
from .utils import (
    get_conn_timeout,
    get_logging,
    ping_ok,
    get_device_grpc_port,
    get_device_username,
    get_device_password,
)
import re

_logger = get_logging().getLogger(__name__)

stubs = {}


def getGrpcStubs(device_ip):
    global stubs
    port = get_device_grpc_port()
    user = get_device_username()
    passwd = get_device_password()
    if None in (port, user, passwd):
        _logger.error(
            "Invalid value port : {}, user : {}, passwd : {}".format(port, user, passwd)
        )
        raise ValueError(
            "Invalid value port : {}, user : {}, passwd : {}".format(port, user, passwd)
        )

    if not ping_ok(device_ip):
        raise Exception("Device %s is not reachable !!" % device_ip)

    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        try:
            sw_cert = ssl.get_server_certificate(
                (device_ip, port), timeout=get_conn_timeout()
            ).encode("utf-8")
            # Option 1
            # creds = grpc.ssl_channel_credentials(root_certificates=sw_cert)
            # stub.Get(GetRequest(path=[path], type=GetRequest.ALL, encoding=JSON_IETF),
            #        metadata=[("username", user),
            #                  ("password", passwd)], )

            # Option 2, In this case need not to send user/pass in metadata in get request.
            def auth_plugin(context, callback):
                callback([("username", user), ("password", passwd)], None)

            creds = grpc.composite_channel_credentials(
                grpc.ssl_channel_credentials(root_certificates=sw_cert),
                grpc.metadata_call_credentials(auth_plugin),
            )

            optns = (("grpc.ssl_target_name_override", "localhost"),)
            channel = grpc.secure_channel(f"{device_ip}:{port}", creds, options=optns)
            stub = gNMIStub(channel)
            stubs[device_ip] = stub
            return stub
        except TimeoutError as te:
            _logger.error(f"Connection Timeout on {device_ip} {te}")
            raise
        except ConnectionRefusedError as cr:
            _logger.error(f"Connection refused by {device_ip} {cr}")
            raise


def send_gnmi_get(device_ip, path: list[Path]):
    op = {}
    try:
        device_gnmi_stub = getGrpcStubs(device_ip)
        resp = (
            device_gnmi_stub.Get(
                GetRequest(path=path, type=GetRequest.ALL, encoding=JSON_IETF),
                timeout=get_conn_timeout(),
            )
            if device_gnmi_stub
            else _logger.error(f"no gnmi stub found for device {device_ip}")
        )
        # resp_cap=device_gnmi_stub.Capabilities(CapabilityRequest())
        # print(resp_cap)
        if resp:
            for n in resp.notification:
                for u in n.update:
                    op.update(json.loads(u.val.json_ietf_val.decode("utf-8")))
        return op
    except Exception as e:
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
    try:
        device_gnmi_stub = getGrpcStubs(device_ip)
        if device_gnmi_stub:
            device_gnmi_stub.Set(req, timeout=get_conn_timeout())
        else:
            _logger.error(f"no gnmi stub found for device {device_ip}")
    except Exception as e:
        _logger.debug(f"{e} \n on device_ip : {device_ip} \n set request : {req}")
        raise


def get_gnmi_path(path: str) -> Path:
    """
    Generates a function comment for the given function body in a markdown code block with the correct language syntax.

    Args:
        path (str): The path to be processed.
        Example : openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/

    Returns:
        Path: The generated gnmi path.

    """
    path = path.strip()
    path_elements = path.split("/")
    gnmi_path = Path(
        target="openconfig",
    )
    for pe_entry in path_elements:
        if pe_entry in ["", "restconf", "data"]:
            continue
        ## When filter key is given
        if "[" in pe_entry and "]" in pe_entry and "=" in pe_entry:
            match = re.search(r"\[(.*?)\]", pe_entry)
            if match:
                key_val = match.group(1)
                try:
                    gnmi_path.elem.append(
                        PathElem(
                            name=pe_entry[: match.start()],
                            key={key_val.split("=")[0]: key_val.split("=")[1]},
                        )
                    )
                except ValueError as ve:
                    _logger.error(
                        f"Invalid property identifier {pe_entry} : {ve} , filter arg should be a dict-> propertykey:value"
                    )
                    raise
        else:
            gnmi_path.elem.append(PathElem(name=pe_entry))
    return gnmi_path

import json
import ssl
from typing import List, Iterator
from urllib.parse import unquote

import grpc
from orca_nw_lib.device_db import get_device_db_obj

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
from .utils import (
    get_logging,
    is_grpc_device_listening,
    get_device_grpc_port,
    get_device_username,
    get_device_password, get_request_timeout,
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

    if not is_grpc_device_listening(device_ip, 10):
        raise Exception("Device %s is not reachable !!" % device_ip)

    if stubs and stubs.get(device_ip):
        return stubs.get(device_ip)
    else:
        try:
            sw_cert = ssl.get_server_certificate(
                (device_ip, port), timeout=get_request_timeout()
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
            stub = gNMIStubExtension(channel)
            stubs[device_ip] = stub
            return stub
        except TimeoutError as te:
            _logger.error(f"Connection Timeout on {device_ip} {te}")
            raise
        except ConnectionRefusedError as cr:
            _logger.error(f"Connection refused by {device_ip} {cr}")
            raise


def send_gnmi_get(device_ip, path: list[Path], resend: bool = False):
    is_device_ready(device_ip)
    op = {}
    try:
        device_gnmi_stub = getGrpcStubs(device_ip)
        resp = (
            device_gnmi_stub.Get(
                GetRequest(path=path, type=GetRequest.ALL, encoding=JSON_IETF),
                timeout=get_request_timeout(),
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
    except grpc.RpcError as e:
        _logger.error("Failed to get details from %s: %s", device_ip, e)
        if e.code() == grpc.StatusCode.UNAVAILABLE:  # check if the device is not ready
            if not resend:
                # remove stub from global stubs
                _logger.debug("Removing stub for %s", device_ip)
                remove_stub(device_ip)

                _logger.info("Resending request to get details from %s", device_ip)
                # send the same request again, it will create a new stub
                return send_gnmi_get(device_ip=device_ip, path=path, resend=True)
            else:
                _logger.error("Device %s is not reachable !!" % device_ip)
                raise
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


def get_gnmi_del_reqs(paths: list[Path]):
    return SetRequest(delete=paths)


def send_gnmi_set(req: SetRequest, device_ip: str, resend: bool = False):
    is_device_ready(device_ip)
    try:
        device_gnmi_stub = getGrpcStubs(device_ip)
        if device_gnmi_stub:
            device_gnmi_stub.Set(req, timeout=get_request_timeout())
        else:
            _logger.error(f"no gnmi stub found for device {device_ip}")
    except grpc.RpcError as e:
        _logger.info("Failed to send set request for device %s" % device_ip)
        if e.code() == grpc.StatusCode.UNAVAILABLE:  # check if the device is not ready
            if not resend:
                # remove the stub from global stubs
                _logger.debug("Removing stub for device %s" % device_ip)
                remove_stub(device_ip)

                _logger.info("Re-sending set request again for device %s" % device_ip)
                # resend the request again, it will create a new stub
                return send_gnmi_set(req=req, device_ip=device_ip, resend=True)
            else:
                _logger.error("Device %s is not reachable !!" % device_ip)
                raise
    except Exception as e:
        _logger.debug(f"{e} \n on device_ip : {device_ip} \n set request : {req}")
        raise


def get_gnmi_path(path: str) -> Path:
    """
    Generates a function comment for the given function body in a markdown code block with the correct language syntax.
    It decodes the encoded values in the filter key.

    Args:
        path (str): The path to be processed.
        Example : openconfig-interfaces:interfaces/interface[name=Vlan1]/openconfig-if-ethernet:ethernet/ipv4/ipv4-address[address=237.84.2.178%2f24]


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
                            key={i.split("=")[0]: unquote(i.split("=")[1]) for i in key_val.split(",")},
                            # decoding encoded value
                        )
                    )
                except ValueError as ve:
                    _logger.error(
                        f"Invalid property identifier {pe_entry} : {ve} , filter arg should be a dict-> propertykey:value"
                    )
                    raise
        elif ("[" in pe_entry and "]" not in pe_entry) or ("[" not in pe_entry and "]" in pe_entry):
            _logger.error(
                f"Invalid property identifier {pe_entry} : filter arg should be a start with [ and end with ]"
            )
            raise ValueError(
                f"Invalid property identifier {pe_entry} : filter arg should be a start with [ and end with ]")
        else:
            gnmi_path.elem.append(PathElem(name=pe_entry))
    return gnmi_path


def is_device_ready(device_ip: str):
    """
    Check if the device is ready or not

    Args:
        device_ip (str): The IP address of the device.

    Returns:
        bool: True if device is ready else False
    """
    devices_data = get_device_db_obj(device_ip)
    devices = devices_data if isinstance(devices_data, list) else [devices_data]

    for device in devices:
        if device is None:
            continue
        system_status = (device.system_status or "").lower()
        if "system is not ready" in system_status:
            raise Exception(f"Device at {device.mgt_ip} is not ready")
    return True


def send_gnmi_subscribe(device_ip: str, subscribe_request: Iterator, resend: bool = False):
    """
    Send the subscribe request to the device. If the device is not ready, it will resend the subscribe request.
    Args:
        device_ip (str): The IP address of the device.
        subscribe_request (Iterator): The subscribe request iterator.
        resend (bool, optional): Resend the subscribe request if device is not ready. Defaults to False.
    """
    is_device_ready(device_ip)
    try:
        device_gnmi_stub = getGrpcStubs(device_ip)
        if device_gnmi_stub:
            return device_gnmi_stub.Subscribe(subscribe_request)
        else:
            _logger.error(f"no gnmi stub found for device {device_ip}")
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:  # check if the device is not ready
            if not resend:
                # remove the device stub
                remove_stub(device_ip)

                # resend the subscribe request, it will try to connect to the device again
                return send_gnmi_subscribe(device_ip=device_ip, subscribe_request=subscribe_request, resend=True)
            else:
                _logger.error("Device %s is not reachable !!" % device_ip)
                raise
    except Exception as e:
        _logger.debug(f"{e} \n on device_ip : {device_ip} \n subscribe request : {subscribe_request}")
        raise


def remove_stub(device_ip: str):
    """
    Remove the device stub from global stubs
    Args:
        device_ip (str): The IP address of the device.
    """
    global stubs
    stub = stubs.pop(device_ip, None)
    if stub:
        stub.channel.close()


class gNMIStubExtension(gNMIStub):
    def __init__(self, channel):
        super().__init__(channel)
        self.channel = channel


def close_all_stubs():
    """
    Close all the stubs.

    Notes:
        This function is mainly used to close all gnmi channels.
        Because when running with celery workers,
        the same channel is used for all the workers, it is creating segmentation fault.

    """
    global stubs
    for i in stubs.values():
        i.channel.close()
    stubs = {}
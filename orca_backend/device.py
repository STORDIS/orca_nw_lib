from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import send_gnmi_get


def getDeviceImgName(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[Path(target='openconfig',
                                                         origin='openconfig-image-management',
                                                         elem=[PathElem(name="image-management", ),
                                                               PathElem(
                                                                   name="global", ),
                                                               PathElem(
                                                                   name="state", ),
                                                               PathElem(
                                                                   name="current", )
                                                               ])])


def getDeviceMgmtIntfcInfo(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[Path(target='openconfig',
                                                         origin='sonic-mgmt-interface',
                                                         elem=[PathElem(name="sonic-mgmt-interface", ),
                                                               ])])
    
    
def getDeviceMetadata(device_ip: str):
    return send_gnmi_get(device_ip=device_ip, path=[Path(target='openconfig',
                                                         origin='sonic-device-metadata',
                                                         elem=[PathElem(name="sonic-device-metadata", ),
                                                               PathElem(name="DEVICE_METADATA", ),
                                                               ])])
from orca_backend.gnmi_pb2 import Path, PathElem
from orca_backend.gnmi_util import send_gnmi_get


def getDeviceDetails(device_ip: str):
    
    '''
    Sample output :
        {'img_name': 'SONiC-OS-4.0.5-Enterprise_Base', 'mgt_intf': 'eth0', 'mgt_ip': '10.10.130.11/23',
        'hwsku': 'DellEMC-S5248f-P-25G-DPB', 'mac': '0c:72:05:74:00:08', 'platform': 'x86_64-kvm_x86_64-r0', 'type': 'LeafRouter'}

    '''
    op_dict = {'img_name': '', 'mgt_intf': '', 'mgt_ip': '',
                'hwsku': '', 'mac': '', 'platform': '', 'type': ''}
    
    
    op1 = getDeviceImgName(device_ip)
    op2 = getDeviceMgmtIntfcInfo(device_ip)
    op3 = getDeviceMetadata(device_ip)
    
    if op1 is not None and op1:
        op_dict['img_name'] = op1.get('openconfig-image-management:current')
    if op2 is not None and op2:
        op_dict['mgt_intf'] = op2.get('sonic-mgmt-interface:sonic-mgmt-interface').get('MGMT_INTF_TABLE').get('MGMT_INTF_TABLE_IPADDR_LIST')[0].get('ifName')
        op_dict['mgt_ip'] = op2.get('sonic-mgmt-interface:sonic-mgmt-interface').get(
            'MGMT_INTF_TABLE').get('MGMT_INTF_TABLE_IPADDR_LIST')[0].get('ipPrefix')
    if op3 is not None and op3:
        op_dict['hwsku'] = op3.get('sonic-device-metadata:DEVICE_METADATA').get('DEVICE_METADATA_LIST')[0].get('hwsku')
        op_dict['mac'] = op3.get('sonic-device-metadata:DEVICE_METADATA').get('DEVICE_METADATA_LIST')[0].get('mac')
        op_dict['platform'] = op3.get('sonic-device-metadata:DEVICE_METADATA').get('DEVICE_METADATA_LIST')[0].get('platform')
        op_dict['type'] = op3.get('sonic-device-metadata:DEVICE_METADATA').get('DEVICE_METADATA_LIST')[0].get('type')
    
    ## Replace None values with empty string
    for key,val in op_dict.items():
        op_dict[key]='' if val is None else val
    return op_dict


def getDeviceImgName(device_ip: str):
    '''
    Sample output :
    {'openconfig-image-management:current': 'SONiC-OS-4.0.5-Enterprise_Advanced'}
    '''

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
    '''
    Sample Output :
    {'sonic-mgmt-interface:sonic-mgmt-interface': {'MGMT_INTF_TABLE': {'MGMT_INTF_TABLE_IPADDR_LIST': [
        {'ifName': 'eth0', 'ipPrefix': '10.10.131.111/23'}, {'ifName': 'eth0', 'ipPrefix': 'fe80::6a21:5fff:fe46:cf6e/64'}]}}}
    '''

    return send_gnmi_get(device_ip=device_ip, path=[Path(target='openconfig',
                                                         origin='sonic-mgmt-interface',
                                                         elem=[PathElem(name="sonic-mgmt-interface", ),
                                                               ])])


def getDeviceMetadata(device_ip: str):
    '''
    Sample Output : 
    {'sonic-device-metadata:DEVICE_METADATA': {'DEVICE_METADATA_LIST': [{'default_config_profile': 'l3', 'hostname': 'sonic',
                                                                         'hwsku': 'Accton-AS7726-32X', 'mac': '68:21:5f:46:cf:71', 'name': 'localhost', 'platform': 'x86_64-accton_as7726_32x-r0', 'type': 'LeafRouter'}]}}
    '''

    return send_gnmi_get(device_ip=device_ip, path=[Path(target='openconfig',
                                                         origin='sonic-device-metadata',
                                                         elem=[PathElem(name="sonic-device-metadata", ),
                                                               PathElem(
                                                                   name="DEVICE_METADATA", ),
                                                               ])])

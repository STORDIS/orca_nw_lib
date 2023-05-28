import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_default_orca_config
load_default_orca_config()

from orca_nw_lib.device import getDeviceDetailsFromGraph, getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo,getDeviceDetails

dut_ip='10.10.130.10'
print(getDeviceDetailsFromGraph())
print(getDeviceImgName(dut_ip))
print(getDeviceMgmtIntfcInfo(dut_ip))
print(getDeviceMetadata(dut_ip))
print(getDeviceDetails(dut_ip))    
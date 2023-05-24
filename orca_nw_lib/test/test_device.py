from test_common import dut_ip
from orca_nw_lib.device import getDeviceDetailsFromGraph, getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo,getDeviceDetails


print(getDeviceDetailsFromGraph())
print(getDeviceImgName(dut_ip))
print(getDeviceMgmtIntfcInfo(dut_ip))
print(getDeviceMetadata(dut_ip))
print(getDeviceDetails(dut_ip))    
from test_common import dut_ip, load_orca_config
load_orca_config()

from orca_backend.device import getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo

print(getDeviceImgName(dut_ip))
print("*****")
print(getDeviceMgmtIntfcInfo(dut_ip))
print("*****")
print(getDeviceMetadata(dut_ip))
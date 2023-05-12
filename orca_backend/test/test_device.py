from test_common import dut_ip
from orca_backend.device import getDeviceDetailsFromDB, getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo,getDeviceDetails


print(getDeviceDetailsFromDB())
print(getDeviceImgName(dut_ip))
print(getDeviceMgmtIntfcInfo(dut_ip))
print(getDeviceMetadata(dut_ip))
print(getDeviceDetails(dut_ip))    
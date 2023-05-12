from test_common import dut_ip
from orca_backend.device import getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo,getDeviceDetails

print(getDeviceImgName(dut_ip))
print(getDeviceMgmtIntfcInfo(dut_ip))
print(getDeviceMetadata(dut_ip))
print(getDeviceDetails(dut_ip))    
from test_common import dut_ip
from orca_backend.utils import load_orca_config
load_orca_config()

from orca_backend.device import getDeviceImgName, getDeviceMetadata,getDeviceMgmtIntfcInfo,wrapper_getDeviceDetails

print(getDeviceImgName(dut_ip))
print(getDeviceMgmtIntfcInfo(dut_ip))
print(getDeviceMetadata(dut_ip))
print(wrapper_getDeviceDetails(dut_ip))    
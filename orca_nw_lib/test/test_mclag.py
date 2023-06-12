import sys
sys.path.append('../orca_nw_lib')
from orca_nw_lib.utils import load_config,load_logging_config
load_config()
load_logging_config()

from orca_nw_lib.mclag import del_mclag, get_mclag_config,config_mclag_domain
dut_ip='10.10.130.12'
print(del_mclag(dut_ip))
print(config_mclag_domain(dut_ip,1,"2.2.2.2","3.3.3.3","PortChannel100","aa:aa:aa:aa:aa:aa",3,3,3))
print(get_mclag_config(dut_ip))
print(del_mclag(dut_ip))
print(get_mclag_config(dut_ip))


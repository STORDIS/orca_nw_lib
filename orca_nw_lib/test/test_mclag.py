from test_common import dut_ip, load_orca_config
load_orca_config()

from orca_nw_lib.mclag import del_mclag, get_mclag_config,config_mclag_domain

print(del_mclag(dut_ip))
print(config_mclag_domain(dut_ip,1,"2.2.2.2","3.3.3.3","PortChannel100","aa:aa:aa:aa:aa:aa",3,3,3))
print(get_mclag_config(dut_ip))
print(del_mclag(dut_ip))
print(get_mclag_config(dut_ip))


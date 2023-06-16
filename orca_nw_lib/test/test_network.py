import re
import sys

sys.path.append("../orca_nw_lib")
from orca_nw_lib.utils import load_config, load_logging_config, ping_ok

load_config()
load_logging_config()
from orca_nw_lib.utils import settings
from orca_nw_lib.constants import network
from orca_nw_lib.discovery import discover_all
from orca_nw_lib.graph_db_utils import (
    getAllDevicesIP,
    getAllInterfacesNameOfDevice,
    getAllInterfacesOfDevice,
)
import unittest
from orca_nw_lib.mclag import (
    config_mclag_domain,
    config_mclag_gateway_mac,
    del_mclag_gateway_mac,
    get_mclag_domain,
    del_mclag,
    get_mclag_config,
    get_mclag_gateway_mac,
)


from orca_nw_lib.interfaces import (
    Speed,
    config_interface,
    get_interface_config,
    get_interface_speed,
    get_interface_status,
)
from orca_nw_lib.port_chnl import (
    add_port_chnl,
    del_port_chnl,
    get_port_chnl,
    add_port_chnl_member,
    get_all_port_chnl_members,
    remove_port_chnl_member,
)


class TestDiscovery(unittest.TestCase):
    def test_discovery():
        discover_all()
        # Not the best way to test but atleast check for if all pingable ips from settings are present in DB
        assert set([ip for ip in settings.get(network) if ping_ok(ip)]).issubset(
            set(getAllDevicesIP())
        )


class InterfaceTests(unittest.TestCase):
    # dut_ip = getAllDevicesIP()[0]
    dut_ip = "10.10.131.111"
    # ethernet = [ether for ether in getAllInterfacesNameOfDevice(dut_ip) if 'Ethernet' in ether][0]
    ethernet = "Ethernet0"

    print(f"{dut_ip}:{ethernet}")

    def test_interface_config(self):
        speed_to_set = Speed.SPEED_10GB
        mtu_to_set = 8000
        enable = False
        loopback = False
        description = "Test Description"
        config_interface(
            self.dut_ip,
            self.ethernet,
            speed=speed_to_set,
            mtu=mtu_to_set,
            description=description,
            loopback=loopback,
            enable=enable,
        )
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert get_interface_speed(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        ) == str(speed_to_set)
        assert config.get("enabled") == enable
        assert config.get("mtu") == mtu_to_set
        assert config.get("enabled") == enable
        assert config.get("description") == description

        mtu_to_set = 9100
        enable = True
        loopback = True
        description = "Test Description 2"
        config_interface(
            self.dut_ip,
            self.ethernet,
            mtu=mtu_to_set,
            description=description,
            loopback=loopback,
            enable=enable,
        )
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == enable
        assert config.get("mtu") == mtu_to_set
        assert config.get("enabled") == enable
        assert config.get("description") == description


class PortChannelTests(unittest.TestCase):
    # dut_ip = getAllDevicesIP()[0]
    dut_ip = "10.10.131.111"
    # ethernet = [ether for ether in getAllInterfacesNameOfDevice(dut_ip) if 'Ethernet' in ether][0]
    ethernet1 = "Ethernet4"
    ethernet2 = "Ethernet8"
    chnl_name = "PortChannel101"

    def test_add_port_chnl(self):
        add_port_chnl(self.dut_ip, self.chnl_name)
        assert (
            get_port_chnl(self.dut_ip, self.chnl_name)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.chnl_name
        )
        del_port_chnl(self.dut_ip, self.chnl_name)

    def test_add_port_chnl_members(self):
        add_port_chnl(self.dut_ip, self.chnl_name, "up")
        assert (
            get_port_chnl(self.dut_ip, self.chnl_name)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.chnl_name
        )

        mem_infcs = [self.ethernet1, self.ethernet2]
        add_port_chnl_member(self.dut_ip, self.chnl_name, mem_infcs)
        output = get_all_port_chnl_members(self.dut_ip)
        output_mem_infcs = []
        for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
            if item.get("name") == self.chnl_name:
                output_mem_infcs.append(item.get("ifname"))

        assert mem_infcs == output_mem_infcs
        del_port_chnl(self.dut_ip, self.chnl_name)

    def test_remove_port_chnl_members(self):
        add_port_chnl(self.dut_ip, self.chnl_name, "up")
        assert (
            get_port_chnl(self.dut_ip, self.chnl_name)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.chnl_name
        )

        mem_infcs = [self.ethernet1, self.ethernet2]
        add_port_chnl_member(self.dut_ip, self.chnl_name, mem_infcs)
        output = get_all_port_chnl_members(self.dut_ip)
        output_mem_infcs = []
        for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
            if item.get("name") == self.chnl_name:
                output_mem_infcs.append(item.get("ifname"))

        assert mem_infcs == output_mem_infcs

        remove_port_chnl_member(self.dut_ip, self.chnl_name, "Ethernet4")

        output = get_all_port_chnl_members(self.dut_ip)
        output_mem_infcs = []
        for item in output.get("sonic-portchannel:PORTCHANNEL_MEMBER_LIST"):
            if item.get("name") == self.chnl_name:
                output_mem_infcs.append(item.get("ifname"))

        assert "Ethernet4" not in output_mem_infcs

        del_port_chnl(self.dut_ip, self.chnl_name)


class MclagTests(unittest.TestCase):
    # dut_ip = getAllDevicesIP()[0]
    dut_ip = "10.10.131.111"
    peer_address = "10.10.131.10"
    peer_link = "PortChannel100"
    mclag_sys_mac = "00:00:00:22:22:22"
    # ethernet = [ether for ether in getAllInterfacesNameOfDevice(dut_ip) if 'Ethernet' in ether][0]
    ethernet = "Ethernet0"
    domain_id = 1

    def test_mclag_domain(self):
        config_mclag_domain(
            self.dut_ip,
            self.domain_id,
            self.dut_ip,
            self.peer_address,
            self.peer_link,
            self.mclag_sys_mac,
        )
        resp = get_mclag_domain(self.dut_ip)
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("domain-id")
            == self.domain_id
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("mclag-system-mac")
            == self.mclag_sys_mac
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0]
            .get("config")
            .get("peer-address")
            == self.peer_address
        )
        assert (
            resp.get("openconfig-mclag:mclag-domain")[0].get("config").get("peer-link")
            == self.peer_link
        )
        del_mclag(self.dut_ip)
        assert not get_mclag_config(self.dut_ip)

    def test_maclag_gateway_mac(self):
        del_mclag_gateway_mac(self.dut_ip)
        assert not get_mclag_gateway_mac(self.dut_ip)
        gw_mac = "aa:bb:aa:bb:aa:bb"
        config_mclag_gateway_mac(self.dut_ip, gw_mac)
        print(get_mclag_gateway_mac(self.dut_ip))
        assert (
            get_mclag_gateway_mac(self.dut_ip)
            .get("openconfig-mclag:mclag-gateway-macs")
            .get("mclag-gateway-mac")[0]
            .get("gateway-mac")
            == gw_mac
        )
        del_mclag_gateway_mac(self.dut_ip)
        assert not get_mclag_gateway_mac(self.dut_ip)
        
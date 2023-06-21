import re
import sys
from orca_nw_lib.common import Speed

from orca_nw_lib.utils import get_orca_config, get_logging, ping_ok
from orca_nw_lib.discovery import discover_all


# import sys
# sys.path.append('../orca_nw_lib')
# discover_all()

from orca_nw_lib.constants import network
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


# @unittest.skip("Because takes too long.")
class TestDiscovery(unittest.TestCase):
    def test_discovery(self):
        discover_all()
        # Not the best way to test but atleast check for if all pingable ips from settings are present in DB
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP()))


class InterfaceTests(unittest.TestCase):
    dut_ip = None
    ethernet = None

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP()))
        cls.dut_ip = getAllDevicesIP()[0]
        cls.ethernet = [
            ether
            for ether in getAllInterfacesNameOfDevice(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        assert cls.dut_ip is not None and cls.ethernet is not None

    def test_interface_mtu(self):
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        mtu_before_test = config.get("mtu")
        mtu_to_set = 9100
        config_interface(self.dut_ip, self.ethernet, mtu=mtu_to_set)
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("mtu") == mtu_to_set
        config_interface(self.dut_ip, self.ethernet, mtu=mtu_before_test)

        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("mtu") == mtu_before_test

    def test_interface_speed(self):
        self.ethernet='Ethernet0'
        speed_before_test = get_interface_speed(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        )
        speed_to_set = Speed.SPEED_10GB
        config_interface(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert get_interface_speed(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        ) == str(speed_to_set)

        speed_to_set = Speed.SPEED_25GB
        config_interface(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert get_interface_speed(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        ) == str(speed_to_set)

        config_interface(self.dut_ip, self.ethernet, speed=speed_before_test)
        assert get_interface_speed(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        ) == str(speed_before_test)

    def test_interface_enable(self):
        enable = False
        config_interface(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == enable

        enable = True
        config_interface(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        config = get_interface_config(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == enable


class PortChannelTests(unittest.TestCase):
    dut_ip = None
    ethernet1 = "Ethernet4"
    ethernet2 = "Ethernet8"
    chnl_name = "PortChannel101"

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP()))
        cls.dut_ip = getAllDevicesIP()[0]
        assert cls.dut_ip is not None

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
    peer_address = None
    peer_link = "PortChannel100"
    mclag_sys_mac = "00:00:00:22:22:22"
    domain_id = 1

    dut_ip = None
    ethernet1 = "Ethernet4"
    ethernet2 = "Ethernet8"

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIP()))
        cls.dut_ip = getAllDevicesIP()[0]
        cls.peer_address = getAllDevicesIP()[0]
        assert cls.dut_ip is not None

    def test_mclag_domain(self):
        del_port_chnl(self.dut_ip, self.peer_link)
        add_port_chnl(self.dut_ip, self.peer_link)
        assert (
            get_port_chnl(self.dut_ip, self.peer_link)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.peer_link
        )
        del_mclag(self.dut_ip)
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

        del_port_chnl(self.dut_ip, self.peer_link)
        assert not get_port_chnl(self.dut_ip, self.peer_link)

    def test_maclag_gateway_mac(self):
        del_mclag_gateway_mac(self.dut_ip)
        assert not get_mclag_gateway_mac(self.dut_ip)
        gw_mac = "aa:bb:aa:bb:aa:bb"
        config_mclag_gateway_mac(self.dut_ip, gw_mac)
        assert (
            get_mclag_gateway_mac(self.dut_ip)
            .get("openconfig-mclag:mclag-gateway-macs")
            .get("mclag-gateway-mac")[0]
            .get("gateway-mac")
            == gw_mac
        )
        del_mclag_gateway_mac(self.dut_ip)
        assert not get_mclag_gateway_mac(self.dut_ip)
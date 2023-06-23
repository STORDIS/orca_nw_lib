import sys
from time import sleep
from orca_nw_lib.common import Speed
from orca_nw_lib.gnmi_sub import gnmi_subscribe, gnmi_unsubscribe

from orca_nw_lib.utils import get_orca_config, ping_ok
from orca_nw_lib.discovery import discover_all

from orca_nw_lib.constants import network
from orca_nw_lib.graph_db_utils import (
    getAllDevicesIPFromDB,
    getAllInterfacesNameOfDeviceFromDB,
    getInterfaceOfDeviceFromDB,
)
import unittest
from orca_nw_lib.mclag import (
    config_mclag_domain,
    config_mclag_gateway_mac,
    config_mclag_mem_portchnl,
    del_mclag_gateway_mac,
    del_mclag_mem_portchnl,
    get_mclag_config,
    get_mclag_domain,
    del_mclag,
    get_mclag_gateway_mac,
    get_mclag_mem_portchnl,
)


from orca_nw_lib.interfaces import (
    get_intfc_speed_path,
    set_interface_config_on_device,
    get_interface_config_from_device,
    get_interface_speed_from_device,
    get_intfc_config_path,
)
from orca_nw_lib.port_chnl import (
    add_port_chnl,
    del_port_chnl,
    get_port_chnl,
    add_port_chnl_member,
    get_all_port_chnl_members,
    remove_port_chnl_member,
)


@unittest.skip("Because takes too long.")
class TestDiscovery(unittest.TestCase):
    def test_discovery(self):
        discover_all()
        # Not the best way to test but atleast check for if all pingable ips from settings are present in DB
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))


class InterfaceTests(unittest.TestCase):
    dut_ip = None
    ethernet = None

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        cls.dut_ip = getAllDevicesIPFromDB()[0]
        cls.ethernet = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        assert cls.dut_ip is not None and cls.ethernet is not None

    def test_interface_mtu(self):
        config = get_interface_config_from_device(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        mtu_before_test = config.get("mtu")
        mtu_to_set = 9100
        set_interface_config_on_device(self.dut_ip, self.ethernet, mtu=mtu_to_set)
        config = get_interface_config_from_device(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("mtu") == mtu_to_set
        set_interface_config_on_device(self.dut_ip, self.ethernet, mtu=mtu_before_test)

        config = get_interface_config_from_device(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("mtu") == mtu_before_test

    def test_interface_speed(self):
        self.ethernet = "Ethernet0"
        speed_before_test = get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
            "openconfig-if-ethernet:port-speed"
        )
        speed_to_set = Speed.SPEED_10GB
        set_interface_config_on_device(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert (
            get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            == speed_to_set.get_gnmi_val()
        )

        speed_to_set = Speed.SPEED_25GB
        set_interface_config_on_device(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert (
            get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            == speed_to_set.get_gnmi_val()
        )

        set_interface_config_on_device(
            self.dut_ip, self.ethernet, speed=Speed[speed_before_test.split(":")[1]]
        )
        assert (
            get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            == speed_before_test
        )

    def test_interface_enable(self):
        enable = False
        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        config = get_interface_config_from_device(self.dut_ip, self.ethernet).get(
            "openconfig-interfaces:config"
        )
        assert config.get("enabled") == enable

        enable = True
        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        config = get_interface_config_from_device(self.dut_ip, self.ethernet).get(
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
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        cls.dut_ip = getAllDevicesIPFromDB()[0]
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
    mem_port_chnl = "PortChannel101"
    mem_port_chnl_2 = "PortChannel102"
    dut_ip = None

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        cls.dut_ip = getAllDevicesIPFromDB()[0]
        cls.peer_address = getAllDevicesIPFromDB()[0]
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

    def test_mclag_mem_port_chnl(self):
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

        del_port_chnl(self.dut_ip, self.mem_port_chnl)
        del_port_chnl(self.dut_ip, self.mem_port_chnl_2)

        add_port_chnl(self.dut_ip, self.mem_port_chnl)
        add_port_chnl(self.dut_ip, self.mem_port_chnl_2)

        assert (
            get_port_chnl(self.dut_ip, self.mem_port_chnl)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.mem_port_chnl
        )

        assert (
            get_port_chnl(self.dut_ip, self.mem_port_chnl_2)
            .get("sonic-portchannel:PORTCHANNEL_LIST")[0]
            .get("name")
            == self.mem_port_chnl_2
        )

        config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl)
        config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl_2)

        assert (
            get_mclag_mem_portchnl(self.dut_ip)
            .get("openconfig-mclag:interface")[0]
            .get("name")
            == self.mem_port_chnl
        )

        assert (
            get_mclag_mem_portchnl(self.dut_ip)
            .get("openconfig-mclag:interface")[1]
            .get("name")
            == self.mem_port_chnl_2
        )

        del_mclag_mem_portchnl(self.dut_ip)

        assert not get_mclag_mem_portchnl(self.dut_ip)

        del_port_chnl(self.dut_ip, self.mem_port_chnl)
        assert not get_port_chnl(self.dut_ip, self.mem_port_chnl)

        del_mclag(self.dut_ip)
        assert not get_mclag_config(self.dut_ip)

        del_port_chnl(self.dut_ip, self.peer_link)
        assert not get_port_chnl(self.dut_ip, self.peer_link)


class SubscriptiosTests(unittest.TestCase):
    dut_ip = None
    ethernet = None

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        cls.dut_ip = getAllDevicesIPFromDB()[0]
        # cls.ethernet = [
        #     ether
        #     for ether in getAllInterfacesNameOfDevice(cls.dut_ip)
        #     if "Ethernet" in ether
        # ][0]
        cls.ethernet = "Ethernet0"
        assert cls.dut_ip is not None and cls.ethernet is not None


    def test_interface_config_update(self):
        sts = gnmi_subscribe(
            self.dut_ip,
            [get_intfc_config_path(self.ethernet)],
        )
        assert sts
        sleep(3)
        enable = not getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).enabled
        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        sleep(1)
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).enabled == enable

        enable = not getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).enabled

        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        sleep(1)
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).enabled == enable
        gnmi_unsubscribe(self.dut_ip)

    def test_interface_speed_update(self):
        sts = gnmi_subscribe(
            self.dut_ip,
            [get_intfc_speed_path(self.ethernet)],
        )
        assert sts
        sleep(2)
        speed = (
            Speed.SPEED_10GB
            if str(Speed.SPEED_25GB)
            in get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            else Speed.SPEED_25GB
        )
        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            speed=speed,
        )
        sleep(2)
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).speed == str(speed)

        speed = (
            Speed.SPEED_10GB
            if str(Speed.SPEED_25GB)
            in get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            else Speed.SPEED_25GB
        )

        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            speed=speed,
        )
        sleep(2)
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).speed == str(speed)
        gnmi_unsubscribe(self.dut_ip)
        
        
# st=SubscriptiosTests()
# st.setUpClass()
# st.test_interface_speed_update()
# st.tearDownClass()
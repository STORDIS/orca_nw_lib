import unittest
from time import sleep
from orca_nw_lib.bgp import (
    configBGPNeighborsOnDevice,
    configBgpGlobalOnDevice,
    del_bgp_global_from_device,
    delAllBgpNeighborsFromDevice,
    get_bgp_global_of_vrf_from_device,
    get_bgp_neighbor_from_device,
)
from orca_nw_lib.common import Speed, VlanTagMode
from orca_nw_lib.device import getAllDevicesIPFromDB
from orca_nw_lib.gnmi_sub import gnmi_subscribe, gnmi_unsubscribe
from orca_nw_lib.mclag import (
    config_mclag,
    config_mclag_gw_mac,
    config_mclag_mem_portchnl,
    del_mclag,
    del_mclag_gw_mac,
    del_mclag_member,
    get_mclag_gw_mac,
    get_mclag_mem_portchnls,
    get_mclags,
)

from orca_nw_lib.port_chnl import (
    add_port_chnl,
    add_port_chnl_mem,
    del_port_chnl,
    del_port_chnl_mem,
    get_port_chnl,
    get_port_chnl_members,
)
from orca_nw_lib.port_chnl_gnmi import del_all_port_chnl

from orca_nw_lib.utils import get_orca_config, ping_ok
from orca_nw_lib.discovery import discover_all

from orca_nw_lib.constants import network
from orca_nw_lib.interfaces import (
    del_all_subinterfaces_of_all_interfaces_from_device,
    del_subinterface_of_interface_from_device,
    get_subinterface_from_device,
    getInterfaceOfDeviceFromDB,
)
from orca_nw_lib.mclag_gnmi import del_mclag_from_device,

from orca_nw_lib.interfaces import (
    getAllInterfacesNameOfDeviceFromDB,
    set_interface_config_on_device,
    get_interface_config_from_device,
    get_interface_speed_from_device,
)
from orca_nw_lib.vlan import (
    add_vlan_mem,
    config_vlan,
    config_vlan_mem_tagging,
    del_vlan,
    del_vlan_mem,
    get_vlan,
    get_vlan_members,
)


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

    @classmethod
    def tearDownClass(cls) -> None:
        gnmi_unsubscribe(cls.dut_ip)

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
        speed_before_test = get_interface_speed_from_device(
            self.dut_ip, self.ethernet
        ).get("openconfig-if-ethernet:port-speed")
        speed_to_set = Speed.SPEED_10GB
        set_interface_config_on_device(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert (
            get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            == speed_to_set.get_oc_val()
        )

        speed_to_set = Speed.SPEED_25GB
        set_interface_config_on_device(self.dut_ip, self.ethernet, speed=speed_to_set)
        assert (
            get_interface_speed_from_device(self.dut_ip, self.ethernet).get(
                "openconfig-if-ethernet:port-speed"
            )
            == speed_to_set.get_oc_val()
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

    def test_interface_ip(self):
        pfx_len = 31
        ip = "1.1.1."
        del_mclag_from_device(self.dut_ip)
        del_all_port_chnl(self.dut_ip)
        for idx in range(0, 1):
            ##Clear IPs from all interfaces on the device inorder to avoid overlapping IP error

            del_all_subinterfaces_of_all_interfaces_from_device(self.dut_ip)
            for intf in (
                get_subinterface_from_device(self.dut_ip, self.ethernet, idx).get(
                    "openconfig-interfaces:subinterface"
                )
                or []
            ):
                assert not intf.get("openconfig-if-ip:ipv4")
            set_interface_config_on_device(
                self.dut_ip,
                self.ethernet,
                ip=f"{ip}{idx}",
                ip_prefix_len=pfx_len,
                index=idx,
            )
            sub_if_config = (
                get_subinterface_from_device(self.dut_ip, self.ethernet, idx)
                .get("openconfig-interfaces:subinterface")[idx]
                .get("openconfig-if-ip:ipv4")
                .get("addresses")
                .get("address")[0]
            )
            assert sub_if_config.get("ip") == f"{ip}{idx}"
            assert sub_if_config.get("config").get("prefix-length") == pfx_len
            del_subinterface_of_interface_from_device(self.dut_ip, self.ethernet, idx)
            for intf in get_subinterface_from_device(
                self.dut_ip, self.ethernet, idx
            ).get("openconfig-interfaces:subinterface"):
                assert not intf.get("openconfig-if-ip:ipv4")

    def test_interface_config_subscription_update(self):
        sts = gnmi_subscribe(self.dut_ip)
        assert sts
        sleep(3)
        enable = not getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).enabled
        set_interface_config_on_device(
            self.dut_ip,
            self.ethernet,
            enable=enable,
        )
        sleep(2)
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

    def test_interface_speed_subscription_update(self):
        self.ethernet = "Ethernet0"

        sts = gnmi_subscribe(self.dut_ip)
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
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).speed == str(
            speed
        )

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
        assert getInterfaceOfDeviceFromDB(self.dut_ip, self.ethernet).speed == str(
            speed
        )
        gnmi_unsubscribe(self.dut_ip)


class PortChannelTests(unittest.TestCase):
    dut_ip = None
    ethernet1 = ""
    ethernet2 = ""
    ethernet3 = ""
    ethernet4 = ""
    chnl_name = "PortChannel101"
    chnl_name_2 = "PortChannel102"

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
        cls.ethernet1 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        cls.ethernet2 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][1]
        cls.ethernet3 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][2]
        cls.ethernet4 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][3]

    def test_add_port_chnl(self):
        ## Cleanup PortChannels
        del_port_chnl(self.dut_ip, self.chnl_name)
        del_port_chnl(self.dut_ip, self.chnl_name_2)
        assert self.chnl_name and self.chnl_name_2 not in [
            chnl.get("lag_name") for chnl in get_port_chnl(self.dut_ip)
        ]
        ## Add PortChannels
        add_port_chnl(self.dut_ip, self.chnl_name)
        add_port_chnl(self.dut_ip, self.chnl_name_2)
        assert self.chnl_name and self.chnl_name_2 in [
            chnl.get("lag_name") for chnl in get_port_chnl(self.dut_ip)
        ]
        ## Cleanup PortChannels
        del_port_chnl(self.dut_ip, self.chnl_name)
        del_port_chnl(self.dut_ip, self.chnl_name_2)
        assert self.chnl_name and self.chnl_name_2 not in [
            chnl.get("lag_name") for chnl in get_port_chnl(self.dut_ip)
        ]

    def test_add_del_port_chnl_members(self):
        ## Cleanup PortChannel 1
        mem_infcs = [self.ethernet1, self.ethernet2]
        for mem_name in mem_infcs:
            del_port_chnl_mem(self.dut_ip, self.chnl_name, mem_name)
        assert not get_port_chnl_members(self.dut_ip, self.chnl_name)
        del_port_chnl(self.dut_ip, self.chnl_name)
        assert not get_port_chnl(self.dut_ip, self.chnl_name)

        ## Cleanup PortChannel 2
        mem_infcs_2 = [self.ethernet3, self.ethernet4]
        for mem_name in mem_infcs_2:
            del_port_chnl_mem(self.dut_ip, self.chnl_name_2, mem_name)
        assert not get_port_chnl_members(self.dut_ip, self.chnl_name_2)
        del_port_chnl(self.dut_ip, self.chnl_name_2)
        assert not get_port_chnl(self.dut_ip, self.chnl_name_2)

        ## Add PortChannel 1
        add_port_chnl(self.dut_ip, self.chnl_name)
        port_chnls = get_port_chnl(self.dut_ip, self.chnl_name)
        assert port_chnls[0].get("lag_name") == self.chnl_name

        add_port_chnl_mem(self.dut_ip, self.chnl_name, mem_infcs)
        port_chnl_mem_json = get_port_chnl_members(self.dut_ip, self.chnl_name)
        assert len(port_chnl_mem_json) == len(mem_infcs)
        for member in port_chnl_mem_json:
            assert member.get("name") in mem_infcs

        ## Add PortChannel 2
        add_port_chnl(self.dut_ip, self.chnl_name_2)
        port_chnls = get_port_chnl(self.dut_ip, self.chnl_name_2)
        assert port_chnls[0].get("lag_name") == self.chnl_name_2

        add_port_chnl_mem(self.dut_ip, self.chnl_name_2, mem_infcs_2)
        port_chnl_mem_json = get_port_chnl_members(self.dut_ip, self.chnl_name_2)
        assert len(port_chnl_mem_json) == len(mem_infcs_2)
        for member in port_chnl_mem_json:
            assert member.get("name") in mem_infcs_2

        ## Cleanup PortChannel 1
        mem_infcs = [self.ethernet1, self.ethernet2]
        for mem_name in mem_infcs:
            del_port_chnl_mem(self.dut_ip, self.chnl_name, mem_name)
        assert not get_port_chnl_members(self.dut_ip, self.chnl_name)
        del_port_chnl(self.dut_ip, self.chnl_name)
        assert not get_port_chnl(self.dut_ip, self.chnl_name)

        ## Cleanup PortChannel 2
        mem_infcs_2 = [self.ethernet3, self.ethernet4]
        for mem_name in mem_infcs_2:
            del_port_chnl_mem(self.dut_ip, self.chnl_name_2, mem_name)
        assert not get_port_chnl_members(self.dut_ip, self.chnl_name_2)
        del_port_chnl(self.dut_ip, self.chnl_name_2)
        assert not get_port_chnl(self.dut_ip, self.chnl_name_2)


class MclagTests(unittest.TestCase):
    peer_address = None
    peer_link = "PortChannel100"
    mclag_sys_mac = "00:00:00:22:22:22"
    domain_id = 1
    mem_port_chnl = "PortChannel101"
    mem_port_chnl_2 = "PortChannel102"
    dut_ip = None
    mclag_gw_mac = "aa:bb:aa:bb:aa:bb"

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
        cls.peer_address = getAllDevicesIPFromDB()[1]
        assert cls.dut_ip is not None

    def test_mclag_domain(self):
        del_port_chnl(self.dut_ip, self.peer_link)
        add_port_chnl(self.dut_ip, self.peer_link)

        for chnl in get_port_chnl(self.dut_ip):
            assert chnl.get("lag_name") == self.peer_link

        del_mclag(self.dut_ip)
        assert not get_mclags(self.dut_ip, self.domain_id)

        config_mclag(
            self.dut_ip,
            self.domain_id,
            self.dut_ip,
            self.peer_address,
            self.peer_link,
            self.mclag_sys_mac,
        )
        for resp in get_mclags(self.dut_ip):
            assert resp["domain_id"] == self.domain_id
            assert resp["peer_addr"] == self.peer_address
            assert resp["peer_link"] == self.peer_link
            assert resp["mclag_sys_mac"] == self.mclag_sys_mac
            assert resp["source_address"] == self.dut_ip

        del_mclag(self.dut_ip)
        assert not get_mclags(self.dut_ip, self.domain_id)

        del_port_chnl(self.dut_ip, self.peer_link)
        assert not get_port_chnl(self.dut_ip, self.peer_link)

    def test_maclag_gateway_mac(self):
        del_mclag_gw_mac(self.dut_ip)
        assert not get_mclag_gw_mac(self.dut_ip)

        gw_mac = "aa:bb:aa:bb:aa:bb"
        config_mclag_gw_mac(self.dut_ip, gw_mac)

        for mac in get_mclag_gw_mac(self.dut_ip):
            assert mac.get("gateway_mac") == gw_mac

        del_mclag_gw_mac(self.dut_ip)
        assert not get_mclag_gw_mac(self.dut_ip)

    def test_mclag_mem_port_chnl(self):
        del_mclag(self.dut_ip)
        del_port_chnl(self.dut_ip, self.peer_link)
        add_port_chnl(self.dut_ip, self.peer_link)

        for chnl in get_port_chnl(self.dut_ip, self.peer_link):
            assert chnl.get("lag_name") == self.peer_link

        config_mclag(
            self.dut_ip,
            self.domain_id,
            self.dut_ip,
            self.peer_address,
            self.peer_link,
            self.mclag_sys_mac,
        )

        for resp in get_mclags(self.dut_ip, self.domain_id):
            assert resp["domain_id"] == self.domain_id
            assert resp["peer_addr"] == self.peer_address
            assert resp["peer_link"] == self.peer_link
            assert resp["mclag_sys_mac"] == self.mclag_sys_mac
            assert resp["source_address"] == self.dut_ip

        del_port_chnl(self.dut_ip, self.mem_port_chnl)
        add_port_chnl(self.dut_ip, self.mem_port_chnl)
        del_port_chnl(self.dut_ip, self.mem_port_chnl_2)
        add_port_chnl(self.dut_ip, self.mem_port_chnl_2)

        config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl)
        config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl_2)

        resp = get_mclag_mem_portchnls(self.dut_ip, self.domain_id)
        assert len(resp) == 2
        for chnl in resp:
            assert chnl.get("lag_name") in [self.mem_port_chnl, self.mem_port_chnl_2]

        del_mclag_member(self.dut_ip)
        assert not get_mclag_mem_portchnls(self.dut_ip, self.domain_id)

        del_port_chnl(self.dut_ip, self.mem_port_chnl)
        del_port_chnl(self.dut_ip, self.mem_port_chnl_2)
        assert not get_port_chnl(self.dut_ip, self.mem_port_chnl)
        assert not get_port_chnl(self.dut_ip, self.mem_port_chnl_2)

        del_mclag(self.dut_ip)
        assert not get_mclags(self.dut_ip)

        del_port_chnl(self.dut_ip, self.peer_link)
        assert not get_port_chnl(self.dut_ip, self.peer_link)


class BGPTests(unittest.TestCase):
    vrf_name = "default"
    dut_ip = ""
    dut_ip_2 = ""
    dut_ip_3 = ""
    asn0 = 65000
    asn1 = 65001
    asn2 = 65002
    bgp_ip_0 = "1.1.1.0"
    bgp_ip_1 = "1.1.1.1"
    bgp_ip_2 = "1.1.1.2"
    bgp_ip_3 = "1.1.1.3"
    afi_safi = "ipv4_unicast"

    @classmethod
    def setUpClass(cls):
        if not set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(getAllDevicesIPFromDB()))
        assert (
            len(set(getAllDevicesIPFromDB())) >= 3
        ), f"Need atleast 3 devices, 1-spine and 2-leaves to run tests, but found : {len(set(getAllDevicesIPFromDB()))}"
        cls.dut_ip = getAllDevicesIPFromDB()[0]
        cls.dut_ip_2 = getAllDevicesIPFromDB()[1]
        cls.dut_ip_3 = getAllDevicesIPFromDB()[2]
        cls.peer_address = getAllDevicesIPFromDB()[0]
        assert cls.dut_ip is not None

    def test_bgp_global_config(self):
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip, self.asn0, self.dut_ip, vrf_name=self.vrf_name
        )
        for bgp_global in (
            get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name).get(
                "sonic-bgp-global:BGP_GLOBALS_LIST"
            )
            or []
        ):
            assert self.asn0 == bgp_global.get("local_asn")
            assert self.dut_ip == bgp_global.get("router_id")
            assert self.vrf_name == bgp_global.get("vrf_name")
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)

    def test_bgp_nbr_config(self):
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)
        configBgpGlobalOnDevice(
            self.dut_ip, self.asn0, self.dut_ip, vrf_name=self.vrf_name
        )
        delAllBgpNeighborsFromDevice(self.dut_ip)
        assert not get_bgp_neighbor_from_device(self.dut_ip)
        configBGPNeighborsOnDevice(self.dut_ip, self.asn1, self.bgp_ip_0, self.vrf_name)
        for nbr in get_bgp_neighbor_from_device(self.dut_ip).get(
            "sonic-bgp-neighbor:BGP_NEIGHBOR_LIST"
        ):
            assert self.asn1 == nbr.get("asn")
            assert self.bgp_ip_0 == nbr.get("neighbor")
            assert self.vrf_name == nbr.get("vrf_name")
        delAllBgpNeighborsFromDevice(self.dut_ip)
        assert not get_bgp_neighbor_from_device(self.dut_ip)
        del_bgp_global_from_device(self.dut_ip, self.vrf_name)
        assert not get_bgp_global_of_vrf_from_device(self.dut_ip, self.vrf_name)


class VLANTests(unittest.TestCase):
    dut_ip = ""
    vlan_name = "Vlan1"
    vlan_id = 1
    eth1 = ""
    eth2 = ""

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
        cls.eth1 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        cls.eth2 = [
            ether
            for ether in getAllInterfacesNameOfDeviceFromDB(cls.dut_ip)
            if "Ethernet" in ether
        ][1]
        assert cls.dut_ip is not None

    def test_vlan_config(self):
        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)

        members_to_add = {
            self.eth1: VlanTagMode.tagged,
            self.eth2: VlanTagMode.untagged,
        }
        config_vlan(self.dut_ip, self.vlan_name, self.vlan_id, members_to_add)

        v = get_vlan(self.dut_ip, self.vlan_name)
        assert v.get("name") == self.vlan_name
        assert v.get("vlanid") == self.vlan_id

        members = get_vlan_members(self.dut_ip, self.vlan_name)

        for mem, tagging_mode in members.items():
            assert members_to_add.get(mem).name == tagging_mode

        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)

    def test_vlan_tagging_mode(self):
        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)

        members_to_add = {
            self.eth1: VlanTagMode.tagged,
            self.eth2: VlanTagMode.untagged,
        }
        config_vlan(self.dut_ip, self.vlan_name, self.vlan_id, members_to_add)
        vlan_detail = get_vlan(self.dut_ip, self.vlan_name)
        assert vlan_detail.get("name") == self.vlan_name
        assert vlan_detail.get("vlanid") == self.vlan_id

        ## Toggle and test tagging mode
        config_vlan_mem_tagging(
            self.dut_ip, self.vlan_name, self.eth1, VlanTagMode.untagged
        )
        config_vlan_mem_tagging(
            self.dut_ip, self.vlan_name, self.eth2, VlanTagMode.tagged
        )

        members = get_vlan_members(self.dut_ip, self.vlan_name)

        for mem, tagging_mode in members.items():
            assert members_to_add.get(mem).name != tagging_mode

        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)

    def test_vlan_mem_add_del(self):
        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)
        config_vlan(self.dut_ip, self.vlan_name, self.vlan_id)
        members_to_add = {
            self.eth1: VlanTagMode.tagged,
            self.eth2: VlanTagMode.untagged,
        }
        add_vlan_mem(self.dut_ip, self.vlan_name, members_to_add)

        members = get_vlan_members(self.dut_ip, self.vlan_name)
        for mem in members:
            assert mem in members_to_add

        del_vlan_mem(self.dut_ip, self.vlan_name, self.eth1)
        members = get_vlan_members(self.dut_ip, self.vlan_name)
        assert self.vlan_name not in members

        del_vlan(self.dut_ip, self.vlan_name)
        assert not get_vlan(self.dut_ip, self.vlan_name)

import random
import unittest

from grpc._channel import _InactiveRpcError
from orca_nw_lib.bgp import (
    config_bgp_global,
    config_bgp_neighbors,
    del_all_bgp_neighbors,
    del_bgp_global,
    get_bgp_global,
    get_bgp_neighbors_subinterfaces,
)
from orca_nw_lib.common import Speed, VlanTagMode
from orca_nw_lib.constants import network
from orca_nw_lib.device_db import get_all_devices_ip_from_db
from orca_nw_lib.discovery import discover_all
from orca_nw_lib.interface import config_interface, del_ip_from_intf, get_interface
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db
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
from orca_nw_lib.utils import get_orca_config, ping_ok
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
        ).issubset(set(get_all_devices_ip_from_db())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))
        cls.dut_ip = get_all_devices_ip_from_db()[0]
        cls.ethernet = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        assert cls.dut_ip is not None and cls.ethernet is not None

    def test_interface_enable_subscription_update(self):
        ##run following code 2 times to ensure the interface has its origional enable state after the test
        for _ in range(2):
            enable_to_set = not get_interface(self.dut_ip, self.ethernet).get(
                "enabled"
            )
            try:
                config_interface(
                    self.dut_ip,
                    self.ethernet,
                    enable=enable_to_set,
                )
            except _InactiveRpcError as err:
                self.fail(err)
            assert (
                get_interface(self.dut_ip, self.ethernet).get("enabled")
                == enable_to_set
            )

    def test_interface_speed_subscription_update(self):
        ##run following code 2 times to ensure the interface has its origional speed after the test
        for _ in range(2):
            speed = get_interface(self.dut_ip, self.ethernet).get("speed")
            speed_to_set = (
                Speed.SPEED_40GB
                if str(Speed.SPEED_100GB) == speed
                else Speed.SPEED_100GB
            )
            try:
                config_interface(
                    self.dut_ip,
                    self.ethernet,
                    speed=speed_to_set,
                )
            except _InactiveRpcError as err:
                self.fail(err)

            assert get_interface(self.dut_ip, self.ethernet).get("speed") == str(
                speed_to_set
            )

    def test_interface_mtu_subscription_update(self):
        for i in range(1, 3):
            mtu_to_set = 9102 - i
            try:
                config_interface(
                    self.dut_ip,
                    self.ethernet,
                    mtu=mtu_to_set,
                )
            except _InactiveRpcError:
                self.fail("Failed to set interface mtu")
            assert get_interface(self.dut_ip, self.ethernet).get("mtu") == mtu_to_set

    def test_interface_description_subscription_update(self):
        for _ in range(2):
            description_to_set = "description_" + str(random.randint(1, 100))
            try:
                config_interface(
                    self.dut_ip,
                    self.ethernet,
                    description=description_to_set,
                )
            except _InactiveRpcError:
                self.fail("Failed to set interface description")
            assert (
                get_interface(self.dut_ip, self.ethernet).get("description")
                == description_to_set
            )


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
        ).issubset(set(get_all_devices_ip_from_db())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))
        cls.dut_ip = get_all_devices_ip_from_db()[0]
        assert cls.dut_ip is not None
        cls.ethernet1 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        cls.ethernet2 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][1]
        cls.ethernet3 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][2]
        cls.ethernet4 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][3]

    def test_add_port_chnl(self):
        try:
            ## Cleanup PortChannels
            del_port_chnl(self.dut_ip, self.chnl_name)
        except _InactiveRpcError as err:
            ## Trying to remove port channels which doesn't exist, which is ok
            assert err.details().lower() == "resource not found"

        try:
            ## Cleanup PortChannels
            del_port_chnl(self.dut_ip, self.chnl_name_2)
        except _InactiveRpcError as err:
            ## Trying to remove port channels which doesn't exist, which is ok
            assert err.details().lower() == "resource not found"

        assert self.chnl_name and self.chnl_name_2 not in [
            chnl.get("lag_name") for chnl in get_port_chnl(self.dut_ip)
        ]

        try:
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
        except _InactiveRpcError as err:
            self.fail(err)

    def test_add_del_port_chnl_members(self):
        ## Cleanup PortChannel 1
        mem_infcs = [self.ethernet1, self.ethernet2]
        mem_infcs_2 = [self.ethernet3, self.ethernet4]
        try:
            del_port_chnl(self.dut_ip)
        except _InactiveRpcError as err:
            ## Trying to remove port channels which doesn't exist, which is ok
            assert err.details().lower() == "resource not found"

        ##Remove IPs from interfaces
        for mem_name in mem_infcs + mem_infcs_2:
            try:
                del_ip_from_intf(self.dut_ip, mem_name)
                ## TODO - Check if speed is same for interfaces going to become member of same port channel
            except _InactiveRpcError as err:
                ## Trying to remove port channels which doesn't exist, which is ok
                assert err.details().lower() == "resource not found"

        try:
            ## Add PortChannel 1
            add_port_chnl(self.dut_ip, self.chnl_name)
            port_chnls = get_port_chnl(self.dut_ip, self.chnl_name)
            assert port_chnls.get("lag_name") == self.chnl_name

            add_port_chnl_mem(self.dut_ip, self.chnl_name, mem_infcs)
            port_chnl_mem_json = get_port_chnl_members(self.dut_ip, self.chnl_name)
            assert len(port_chnl_mem_json) == len(mem_infcs)
            for member in port_chnl_mem_json:
                assert member.get("name") in mem_infcs

            ## Add PortChannel 2
            add_port_chnl(self.dut_ip, self.chnl_name_2)
            port_chnls = get_port_chnl(self.dut_ip, self.chnl_name_2)
            assert port_chnls.get("lag_name") == self.chnl_name_2

            add_port_chnl_mem(self.dut_ip, self.chnl_name_2, mem_infcs_2)
            port_chnl_mem_json = get_port_chnl_members(self.dut_ip, self.chnl_name_2)
            assert len(port_chnl_mem_json) == len(mem_infcs_2)
            for member in port_chnl_mem_json:
                assert member.get("name") in mem_infcs_2

            ## Cleanup PortChannel 1
            for mem_name in mem_infcs:
                del_port_chnl_mem(self.dut_ip, self.chnl_name, mem_name)
            del_port_chnl(self.dut_ip, self.chnl_name)
            assert not get_port_chnl_members(self.dut_ip, self.chnl_name)
            assert not get_port_chnl(self.dut_ip, self.chnl_name)
            ## Cleanup PortChannel 2
            for mem_name in mem_infcs_2:
                del_port_chnl_mem(self.dut_ip, self.chnl_name_2, mem_name)
            assert not get_port_chnl_members(self.dut_ip, self.chnl_name_2)
            del_port_chnl(self.dut_ip, self.chnl_name_2)
            assert not get_port_chnl(self.dut_ip, self.chnl_name_2)
        except _InactiveRpcError as err:
            self.fail(err)


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
        ).issubset(set(get_all_devices_ip_from_db())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))
        cls.dut_ip = get_all_devices_ip_from_db()[0]
        cls.peer_address = get_all_devices_ip_from_db()[1]
        assert cls.dut_ip is not None

    def test_mclag_domain(self):
        try:
            del_mclag(self.dut_ip)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
        assert not get_mclags(self.dut_ip, self.domain_id)
        
        try:
            del_port_chnl(self.dut_ip, self.peer_link)
        except _InactiveRpcError as err:
            ## Trying to remove port channels which doesn't exist, which is ok
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip, self.peer_link)
        except _InactiveRpcError as err:
            self.fail(err)

        chnl = get_port_chnl(self.dut_ip, self.peer_link)
        assert chnl.get("lag_name") == self.peer_link

        try:
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
        except _InactiveRpcError as err:
            self.fail(err)

    def test_maclag_gateway_mac(self):
        try:
            del_mclag_gw_mac(self.dut_ip)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_mclag_gw_mac(self.dut_ip)

        gw_mac = "aa:bb:aa:bb:aa:bb"
        try:
            config_mclag_gw_mac(self.dut_ip, gw_mac)

            for mac in get_mclag_gw_mac(self.dut_ip):
                assert mac.get("gateway_mac") == gw_mac

            del_mclag_gw_mac(self.dut_ip)
            assert not get_mclag_gw_mac(self.dut_ip)
        except _InactiveRpcError as err:
            self.fail(err)

    def test_mclag_mem_port_chnl(self):
        try:
            del_mclag(self.dut_ip)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            del_port_chnl(self.dut_ip, self.peer_link)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip, self.peer_link)

            chnl = get_port_chnl(self.dut_ip, self.peer_link)
            assert chnl.get("lag_name") == self.peer_link

            config_mclag(
                self.dut_ip,
                self.domain_id,
                self.dut_ip,
                self.peer_address,
                self.peer_link,
                self.mclag_sys_mac,
            )

            resp = get_mclags(self.dut_ip, self.domain_id)
            assert resp["domain_id"] == self.domain_id
            assert resp["peer_addr"] == self.peer_address
            assert resp["peer_link"] == self.peer_link
            assert resp["mclag_sys_mac"] == self.mclag_sys_mac
            assert resp["source_address"] == self.dut_ip
            try:
                del_port_chnl(self.dut_ip, self.mem_port_chnl)
            except _InactiveRpcError as err:
                assert err.details().lower() == "resource not found"
                
            add_port_chnl(self.dut_ip, self.mem_port_chnl)
            try:
                del_port_chnl(self.dut_ip, self.mem_port_chnl_2)
            except _InactiveRpcError as err:
                assert err.details().lower() == "resource not found"
                
            add_port_chnl(self.dut_ip, self.mem_port_chnl_2)

            config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl)
            config_mclag_mem_portchnl(self.dut_ip, self.domain_id, self.mem_port_chnl_2)

            resp = get_mclag_mem_portchnls(self.dut_ip, self.domain_id)
            assert len(resp) == 2
            for chnl in resp:
                assert chnl.get("lag_name") in [
                    self.mem_port_chnl,
                    self.mem_port_chnl_2,
                ]

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
        except _InactiveRpcError as err:
            self.fail(err)


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
        ).issubset(set(get_all_devices_ip_from_db())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))
        assert (
            len(set(get_all_devices_ip_from_db())) >= 3
        ), f"Need atleast 3 devices, 1-spine and 2-leaves to run tests, but found : {len(set(get_all_devices_ip_from_db()))}"
        cls.dut_ip = get_all_devices_ip_from_db()[0]
        cls.dut_ip_2 = get_all_devices_ip_from_db()[1]
        cls.dut_ip_3 = get_all_devices_ip_from_db()[2]
        cls.peer_address = get_all_devices_ip_from_db()[0]
        assert cls.dut_ip is not None

    def test_bgp_global_config(self):
        try:
            del_bgp_global(self.dut_ip, self.vrf_name)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
            
        assert not get_bgp_global(self.dut_ip, self.vrf_name)
        try:
            config_bgp_global(self.dut_ip, self.asn0, self.dut_ip, vrf_name=self.vrf_name)

            bgp_global = get_bgp_global(self.dut_ip, self.vrf_name)
            assert self.asn0 == bgp_global.get("local_asn")
            assert self.dut_ip == bgp_global.get("router_id")
            assert self.vrf_name == bgp_global.get("vrf_name")

            del_bgp_global(self.dut_ip, self.vrf_name)
            assert not get_bgp_global(self.dut_ip, self.vrf_name)
        except _InactiveRpcError as err:
            self.fail(err)

    def test_bgp_nbr_config(self):
        try:
            del_bgp_global(self.dut_ip, self.vrf_name)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
            
        assert not get_bgp_global(self.dut_ip, self.vrf_name)
        
        try:
            config_bgp_global(self.dut_ip, self.asn0, self.dut_ip, vrf_name=self.vrf_name)
            try:
                del_all_bgp_neighbors(self.dut_ip)
            except _InactiveRpcError as err:
                assert err.details().lower() == "resource not found"
                
            assert not get_bgp_neighbors_subinterfaces(self.dut_ip, self.asn0)

            config_bgp_neighbors(self.dut_ip, self.asn1, self.bgp_ip_0, self.vrf_name)
            for nbr in get_bgp_neighbors_subinterfaces(self.dut_ip, self.asn0):
                assert self.bgp_ip_0 == nbr.get("ip_address")

            del_all_bgp_neighbors(self.dut_ip)
            assert not get_bgp_neighbors_subinterfaces(self.dut_ip, self.asn0)
            del_bgp_global(self.dut_ip, self.vrf_name)
            assert not get_bgp_global(self.dut_ip, self.vrf_name)
        except _InactiveRpcError as err:
            self.fail(err)

    # TODO - Test global and neighbour AF, Test adding and removal of neighbors. Deletion of BGP_GLOBAL_AF, MCLAG_GW_MAC and subinterfaces.
    
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
        ).issubset(set(get_all_devices_ip_from_db())):
            discover_all()
        assert set(
            [ip for ip in get_orca_config().get(network) if ping_ok(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))
        cls.dut_ip = get_all_devices_ip_from_db()[0]
        cls.eth1 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][0]
        cls.eth2 = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip)
            if "Ethernet" in ether
        ][1]
        assert cls.dut_ip is not None

    def test_vlan_config(self):
        try:
            del_vlan(self.dut_ip, self.vlan_name)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
            
        assert not get_vlan(self.dut_ip, self.vlan_name)

        members_to_add = {
            self.eth1: VlanTagMode.tagged,
            self.eth2: VlanTagMode.untagged,
        }
        try:
            config_vlan(self.dut_ip, self.vlan_name, self.vlan_id, members_to_add)

            v = get_vlan(self.dut_ip, self.vlan_name)
            assert v.get("name") == self.vlan_name
            assert v.get("vlanid") == self.vlan_id

            members = get_vlan_members(self.dut_ip, self.vlan_name)

            for mem, tagging_mode in members.items():
                assert members_to_add.get(mem).name == tagging_mode

            del_vlan(self.dut_ip, self.vlan_name)
            assert not get_vlan(self.dut_ip, self.vlan_name)
        except _InactiveRpcError as err:
            self.fail(err)

    def test_vlan_tagging_mode(self):
        try:
            del_vlan(self.dut_ip, self.vlan_name)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
        assert not get_vlan(self.dut_ip, self.vlan_name)

        members_to_add = {
            self.eth1: VlanTagMode.tagged,
            self.eth2: VlanTagMode.untagged,
        }
        try:
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
        except _InactiveRpcError as err:
            self.fail(err)

    def test_vlan_mem_add_del(self):
        try:
            del_vlan(self.dut_ip, self.vlan_name)
        except _InactiveRpcError as err:
            assert err.details().lower() == "resource not found"
            
        assert not get_vlan(self.dut_ip, self.vlan_name)
        try:
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
        except _InactiveRpcError as err:
            self.fail(err)

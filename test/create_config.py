import unittest
import time
from grpc import RpcError
from orca_nw_lib.bgp import (
    config_bgp_global,
    config_bgp_global_af,
    config_bgp_neighbor_af,
    config_bgp_neighbors,
    del_all_bgp_neighbors,
    del_bgp_global,
    del_all_bgp_neighbour_af,
    del_bgp_global_af_all,
    get_bgp_global,
    get_bgp_global_af_list,
    get_bgp_neighbors_subinterfaces,
    get_neighbour_bgp,
)
from orca_nw_lib.common import VlanTagMode
from orca_nw_lib.device_db import get_all_devices_ip_from_db
from orca_nw_lib.interface import (
    config_interface,
    del_all_subinterfaces_of_interface,
    get_interface,
    get_subinterfaces,
)
from orca_nw_lib.interface_db import get_all_interfaces_name_of_device_from_db
from orca_nw_lib.mclag import (
    config_mclag,
    config_mclag_gw_mac,
    config_mclag_mem_portchnl,
    del_mclag,
    del_mclag_gw_mac,
    get_mclag_gw_mac,
    get_mclags,
)

from orca_nw_lib.port_chnl import (
    add_port_chnl,
    add_port_chnl_mem,
    del_port_chnl,
    get_port_chnl,
    get_port_chnl_members,
)

from orca_nw_lib.utils import (
    clean_db,
    get_networks,
)
from orca_nw_lib.discovery import discover_device_from_config

from orca_nw_lib.mclag_gnmi import (
    del_mclag_from_device,
)

from orca_nw_lib.vlan import config_vlan, del_vlan, get_vlan, get_vlan_members
from test_network import device_pingable

class SampleConfigDiscovery(unittest.TestCase):
    vrf_name = "default"
    dut_ip_1 = None
    dut_ip_2 = None
    dut_ip_3 = None
    asn0 = 65000
    asn1 = 65001
    asn2 = 65002
    bgp_ip_0 = "1.1.1.0"
    bgp_ip_1 = "1.1.1.1"
    bgp_ip_2 = "1.1.1.2"
    bgp_ip_3 = "1.1.1.3"
    afi_safi = "ipv4_unicast"
    port_chnl_103 = "PortChannel103"
    peer_link_chnl_100 = "PortChannel100"
    mem_port_chnl_101 = "PortChannel101"
    mem_port_chnl_102 = "PortChannel102"
    domain_id = 1
    mclag_sys_mac = "00:00:00:22:22:22"
    ethernet0 = None
    ethernet1 = None
    ethernet2 = None
    ethernet3 = None
    ethernet4 = None
    ethernet5 = None
    ethernet6 = None
    ethernet7 = None
    vlan_name = "Vlan1"
    vlan_name_2 = "Vlan2"
    vlan_name_3 = "Vlan3"
    
    vlan_id = 1
    vlan_id_2 = 2
    vlan_id_3 = 3
    
    @classmethod
    def setUpClass(cls):
        clean_db()
        assert not get_all_devices_ip_from_db()
        orca_config_discovered = lambda: set(
            [ip for ip in get_networks() if device_pingable(ip)]
        ).issubset(set(get_all_devices_ip_from_db()))

        minimum_device_discovered = lambda: len(get_all_devices_ip_from_db()) >= 3

        if not orca_config_discovered() or not minimum_device_discovered():
            discover_device_from_config()
        assert orca_config_discovered()
        assert (
            minimum_device_discovered()
        ), "Need atleast 3 devices, 1-spine and 2-leaves to run tests."
        all_device_list = get_all_devices_ip_from_db()
        cls.dut_ip_1 = all_device_list[0]
        cls.dut_ip_2 = all_device_list[1]
        cls.dut_ip_3 = all_device_list[2]

        all_interface = [
            ether
            for ether in get_all_interfaces_name_of_device_from_db(cls.dut_ip_1)
            if "Ethernet" in ether
        ]
        cls.ethernet0 = all_interface[0]
        cls.ethernet1 = all_interface[1]
        cls.ethernet2 = all_interface[2]
        cls.ethernet3 = all_interface[3]
        cls.ethernet4 = all_interface[4]
        cls.ethernet5 = all_interface[5]
        cls.ethernet6 = all_interface[6]
        cls.ethernet7 = all_interface[7]

        assert cls.dut_ip_1 is not None

        ## cleanup existing configurations
        for dut in [cls.dut_ip_1, cls.dut_ip_2, cls.dut_ip_3]:
            try:
                del_bgp_global(dut, cls.vrf_name)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            try:
                del_mclag(dut)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            try:
                [
                    del_port_chnl(dut, chnl)
                    for chnl in [
                        cls.port_chnl_103,
                        cls.peer_link_chnl_100,
                        cls.mem_port_chnl_101,
                        cls.mem_port_chnl_102,
                    ]
                ]
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            for vlan in [cls.vlan_name_2, cls.vlan_name_3]:
                try:
                    del_vlan(dut, vlan)
                except RpcError as err:
                    assert err.details().lower() == "resource not found"

    @classmethod
    def tearDownClass(cls):
        ## Execute tests again to test any possible errors while overwritting DB.
        cls.test_create_port_channel_config(cls)
        cls.test_create_mclag_configuration(cls)
        cls.test_create_bgp_config(cls)
        cls.test_create_vlan_config(cls)

    def test_create_port_channel_config(self):
        for dut in [self.dut_ip_1, self.dut_ip_2, self.dut_ip_3]:
            try:
                del_port_chnl(dut, self.port_chnl_103)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            try:
                add_port_chnl(dut, self.port_chnl_103, admin_status="up")
                chnl = get_port_chnl(dut, self.port_chnl_103)
                assert chnl.get("lag_name") == self.port_chnl_103
                mem_infcs = [self.ethernet2, self.ethernet3]
                add_port_chnl_mem(dut, self.port_chnl_103, mem_infcs)
                members = get_port_chnl_members(dut, self.port_chnl_103)
                for mem in members:
                    assert mem.get("name") in mem_infcs
            except RpcError as err:
                self.fail(err.details())

    def test_create_mclag_configuration(self):
        ## On device -1 mclag config
        try:
            del_mclag(self.dut_ip_1)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            del_port_chnl(self.dut_ip_1, self.peer_link_chnl_100)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip_1, self.peer_link_chnl_100)
            assert (
                get_port_chnl(self.dut_ip_1, self.peer_link_chnl_100).get("lag_name")
                == self.peer_link_chnl_100
            )
            config_mclag(
                self.dut_ip_1,
                self.domain_id,
                self.dut_ip_1,
                self.dut_ip_2,
                self.peer_link_chnl_100,
                self.mclag_sys_mac,
            )

            resp = get_mclags(self.dut_ip_1, domain_id=self.domain_id)
            assert resp.get("domain_id") == self.domain_id
            assert resp.get("mclag_sys_mac") == self.mclag_sys_mac
            assert resp.get("peer_addr") == self.dut_ip_2
            assert resp.get("peer_link") == self.peer_link_chnl_100
        except RpcError as err:
            self.fail(err)
        ## member configuration
        try:
            del_port_chnl(self.dut_ip_1, chnl_name=self.mem_port_chnl_101)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            del_port_chnl(self.dut_ip_1, chnl_name=self.mem_port_chnl_102)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip_1, self.mem_port_chnl_101)
            add_port_chnl(self.dut_ip_1, self.mem_port_chnl_102)

            config_mclag_mem_portchnl(
                self.dut_ip_1, self.domain_id, self.mem_port_chnl_101
            )
            config_mclag_mem_portchnl(
                self.dut_ip_1, self.domain_id, self.mem_port_chnl_102
            )
        except RpcError as err:
            self.fail(err)

            ## On device -2 mclag config
        try:
            del_mclag_from_device(self.dut_ip_2)
        except RpcError as err:
            assert err.details().lower() == "resource not found"
        try:
            del_port_chnl(self.dut_ip_2, self.peer_link_chnl_100)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip_2, self.peer_link_chnl_100)
            assert (
                get_port_chnl(self.dut_ip_2, self.peer_link_chnl_100).get("lag_name")
                == self.peer_link_chnl_100
            )

            config_mclag(
                self.dut_ip_2,
                self.domain_id,
                self.dut_ip_2,
                self.dut_ip_1,
                self.peer_link_chnl_100,
                self.mclag_sys_mac,
            )

            resp = get_mclags(self.dut_ip_2, self.domain_id)
            assert resp.get("domain_id") == self.domain_id
            assert resp.get("mclag_sys_mac") == self.mclag_sys_mac
            assert resp.get("peer_addr") == self.dut_ip_1
            assert resp.get("peer_link") == self.peer_link_chnl_100
        except RpcError as err:
            self.fail(err)
        ## member configuration
        try:
            del_port_chnl(self.dut_ip_2, self.mem_port_chnl_101)
        except RpcError as err:
            assert err.details().lower() == "resource not found"
        try:
            del_port_chnl(self.dut_ip_2, self.mem_port_chnl_102)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            add_port_chnl(self.dut_ip_2, self.mem_port_chnl_101)
            add_port_chnl(self.dut_ip_2, self.mem_port_chnl_102)

            config_mclag_mem_portchnl(
                self.dut_ip_2, self.domain_id, self.mem_port_chnl_101
            )
            config_mclag_mem_portchnl(
                self.dut_ip_2, self.domain_id, self.mem_port_chnl_102
            )
        except RpcError as err:
            self.fail(err)

            ## Create MCLAG GW mac
        try:
            del_mclag_gw_mac(self.dut_ip_1)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_mclag_gw_mac(self.dut_ip_1)
        gw_mac = "aa:bb:aa:bb:aa:bb"
        try:
            config_mclag_gw_mac(self.dut_ip_1, gw_mac)
        except RpcError as err:
            self.fail(err)
        assert get_mclag_gw_mac(self.dut_ip_1, gw_mac).get("gateway_mac") == gw_mac

    def test_create_bgp_config(self):
        try:
            del_bgp_global(self.dut_ip_1, self.vrf_name)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_global(self.dut_ip_1, self.vrf_name)

        pfxLen = 31
        idx = 0
        ##Clear IPs from all interfaces on the device in order to avoid overlapping IP error
        ## IP config is not permitted on port channel member port, which are configured in port channel test
        for ether in [
            self.ethernet0,
            self.ethernet1,
            self.ethernet4,
            self.ethernet5,
            self.ethernet6,
            self.ethernet7,
        ]:
            try:
                del_all_subinterfaces_of_interface(self.dut_ip_1, ether)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            try:
                del_all_subinterfaces_of_interface(self.dut_ip_2, ether)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            try:
                del_all_subinterfaces_of_interface(self.dut_ip_3, ether)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

        try:
            ############################ Setup two interfaces on spine #######################
            ##################### Setup first interface

            config_interface(
                device_ip=self.dut_ip_1,
                if_name=self.ethernet0,
                ip=self.bgp_ip_1,
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True,
            )
            ##sleep because interface subscription updates are received asynchronously in different thread.
            ## Better approach is implemented in orca_backend tests, where assert is done with timeout and retry.
            time.sleep(5)
            assert get_interface(self.dut_ip_1, self.ethernet0).get("enabled") == True
            assert (
                get_subinterfaces(self.dut_ip_1, self.ethernet0)[0].get("ip_address")
                == self.bgp_ip_1
            )

            ##################### Setup second interface
            config_interface(
                device_ip=self.dut_ip_1,
                if_name=self.ethernet1,
                ip=self.bgp_ip_2,
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True,
            )
            time.sleep(5)
            assert get_interface(self.dut_ip_1, self.ethernet1).get("enabled") == True
            assert (
                get_subinterfaces(self.dut_ip_1, self.ethernet1)[0].get("ip_address")
                == self.bgp_ip_2
            )

            ############################ Setup one interfaces on leaf-1 #######################

            config_interface(
                device_ip=self.dut_ip_2,
                if_name=self.ethernet0,
                ip=self.bgp_ip_0,
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True,
            )
            time.sleep(5)
            assert get_interface(self.dut_ip_2, self.ethernet0).get("enabled") == True
            assert (
                get_subinterfaces(self.dut_ip_2, self.ethernet0)[0].get("ip_address")
                == self.bgp_ip_0
            )

            ############################ Setup one interfaces on leaf-2 #######################

            config_interface(
                device_ip=self.dut_ip_3,
                if_name=self.ethernet0,
                ip=self.bgp_ip_3,
                ip_prefix_len=pfxLen,
                index=idx,
                enable=True,
            )
            time.sleep(5)
            assert get_interface(self.dut_ip_3, self.ethernet0).get("enabled") == True
            assert (
                get_subinterfaces(self.dut_ip_3, self.ethernet0)[0].get("ip_address")
                == self.bgp_ip_3
            )
        except RpcError as err:
            self.fail(err)

        ################# Configure BGP on spine #################
        try:
            del_bgp_global(self.dut_ip_1, self.vrf_name)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_global(self.dut_ip_1, self.vrf_name)

        try:
            config_bgp_global(
                self.dut_ip_1, self.asn0, self.dut_ip_1, vrf_name=self.vrf_name
            )
        except RpcError as err:
            self.fail(err)

        bgp_global = get_bgp_global(self.dut_ip_1, self.vrf_name)
        assert self.asn0 == bgp_global.get("local_asn")
        assert self.dut_ip_1 == bgp_global.get("router_id")
        assert self.vrf_name == bgp_global.get("vrf_name")

        ################# Configure BGP on leaf-1 #################

        try:
            del_bgp_global(self.dut_ip_2, self.vrf_name)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_global(self.dut_ip_2, self.vrf_name)

        try:
            config_bgp_global(
                self.dut_ip_2, self.asn1, self.dut_ip_2, vrf_name=self.vrf_name
            )
        except RpcError as err:
            self.fail(err)

        bgp_global = get_bgp_global(self.dut_ip_2, self.vrf_name)
        assert self.asn1 == bgp_global.get("local_asn")
        assert self.dut_ip_2 == bgp_global.get("router_id")
        assert self.vrf_name == bgp_global.get("vrf_name")

        ################# Configure BGP on leaf-2 #################

        try:
            del_bgp_global(self.dut_ip_3, self.vrf_name)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_global(self.dut_ip_3, self.vrf_name)
        try:
            config_bgp_global(
                self.dut_ip_3, self.asn2, self.dut_ip_3, vrf_name=self.vrf_name
            )
        except RpcError as err:
            self.fail(err)

        bgp_global = get_bgp_global(self.dut_ip_3, self.vrf_name)
        assert self.asn2 == bgp_global.get("local_asn")
        assert self.dut_ip_3 == bgp_global.get("router_id")
        assert self.vrf_name == bgp_global.get("vrf_name")

        ############################ Config bgp global AF on all nodes ####################
        for dev in [self.dut_ip_2, self.dut_ip_1, self.dut_ip_3]:
            try:
                del_bgp_global_af_all(dev)
            except RpcError as err:
                assert err.details().lower() == "resource not found"

            assert not get_bgp_global_af_list(dev)

            try:
                config_bgp_global_af(dev, self.afi_safi, self.vrf_name)
            except RpcError as err:
                self.fail(err)

            for af in get_bgp_global_af_list(dev) or []:
                assert af.get("afi_safi") == self.afi_safi
                assert af.get("vrf_name") == self.vrf_name
        ############################ Setup neighbor and neighbor AF on Spine #######################
        try:
            del_all_bgp_neighbors(self.dut_ip_1)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_neighbors_subinterfaces(self.dut_ip_1, self.asn0)
        assert not get_neighbour_bgp(self.dut_ip_1, self.asn0)

        try:
            config_bgp_neighbors(self.dut_ip_1, self.asn1, self.bgp_ip_0, self.vrf_name)
            config_bgp_neighbors(self.dut_ip_1, self.asn2, self.bgp_ip_3, self.vrf_name)
        except RpcError as err:
            self.fail(err)

        for nbr_subinterface in get_bgp_neighbors_subinterfaces(
            self.dut_ip_1, self.asn0
        ):
            assert nbr_subinterface.get("ip_address") in [self.bgp_ip_0, self.bgp_ip_3]

        for nbr_bgp in get_neighbour_bgp(self.dut_ip_1, self.asn0):
            assert nbr_bgp.get("local_asn") in [self.asn1, self.asn2]

        try:
            del_all_bgp_neighbour_af(self.dut_ip_1)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        for nbr in get_bgp_global(self.dut_ip_1, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert not nbr.get("afi_safi")

        try:
            config_bgp_neighbor_af(
                self.dut_ip_1, self.afi_safi, self.bgp_ip_0, self.vrf_name, True
            )
            config_bgp_neighbor_af(
                self.dut_ip_1, self.afi_safi, self.bgp_ip_3, self.vrf_name, True
            )
        except RpcError as err:
            self.fail(err)

        for nbr in get_bgp_global(self.dut_ip_1, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert {"ipv4_unicast": True} in nbr.get("afi_safi")

        ############################ Setup neighbor and neighbor AF on Leaf-1 #######################
        try:
            del_all_bgp_neighbors(self.dut_ip_2)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_neighbors_subinterfaces(self.dut_ip_2, self.asn1)
        assert not get_neighbour_bgp(self.dut_ip_2, self.asn1)
        try:
            config_bgp_neighbors(self.dut_ip_2, self.asn0, self.bgp_ip_1, self.vrf_name)
        except RpcError as err:
            self.fail(err)

        for nbr_subinterface in get_bgp_neighbors_subinterfaces(
            self.dut_ip_2, self.asn1
        ):
            assert nbr_subinterface.get("ip_address") == self.bgp_ip_1

        for nbr_bgp in get_neighbour_bgp(self.dut_ip_2, self.asn1):
            assert nbr_bgp.get("local_asn") == self.asn0

        try:
            del_all_bgp_neighbour_af(self.dut_ip_2)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        for nbr in get_bgp_global(self.dut_ip_2, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert not nbr.get("afi_safi")

        try:
            config_bgp_neighbor_af(
                self.dut_ip_2, self.afi_safi, self.bgp_ip_1, self.vrf_name, True
            )
        except RpcError as err:
            self.fail(err)

        for nbr in get_bgp_global(self.dut_ip_2, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert {"ipv4_unicast": True} in nbr.get("afi_safi")

        ############################ Setup neighbor and neighbor AF on Leaf-2 #######################

        try:
            del_all_bgp_neighbors(self.dut_ip_3)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_bgp_neighbors_subinterfaces(self.dut_ip_3, self.asn2)
        assert not get_neighbour_bgp(self.dut_ip_3, self.asn2)
        try:
            config_bgp_neighbors(self.dut_ip_3, self.asn0, self.bgp_ip_2, self.vrf_name)
        except RpcError as err:
            self.fail(err)

        for nbr_subinterface in get_bgp_neighbors_subinterfaces(
            self.dut_ip_3, self.asn2
        ):
            assert nbr_subinterface.get("ip_address") == self.bgp_ip_2

        for nbr_bgp in get_neighbour_bgp(self.dut_ip_3, self.asn2):
            assert nbr_bgp.get("local_asn") == self.asn0

        try:
            del_all_bgp_neighbour_af(self.dut_ip_3)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        for nbr in get_bgp_global(self.dut_ip_3, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert not nbr.get("afi_safi")

        try:
            config_bgp_neighbor_af(
                self.dut_ip_3, self.afi_safi, self.bgp_ip_2, self.vrf_name, True
            )
        except RpcError as err:
            self.fail(err)

        for nbr in get_bgp_global(self.dut_ip_3, vrf_name="default").get(
            "neighbor_prop"
        ):
            assert {"ipv4_unicast": True} in nbr.get("afi_safi")

    def test_create_vlan_config(self):
        try:
            del_vlan(self.dut_ip_1, self.vlan_name_2)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        try:
            del_vlan(self.dut_ip_1, self.vlan_name_3)
        except RpcError as err:
            assert err.details().lower() == "resource not found"

        assert not get_vlan(self.dut_ip_1, self.vlan_name_2)
        assert not get_vlan(self.dut_ip_1, self.vlan_name_3)

        mem = {self.ethernet4: VlanTagMode.tagged, self.ethernet5: VlanTagMode.untagged}
        mem_2 = {
            self.ethernet6: VlanTagMode.tagged,
            self.ethernet7: VlanTagMode.untagged,
        }
        try:
            config_vlan(self.dut_ip_1, self.vlan_name_2, self.vlan_id_2, mem)
            config_vlan(self.dut_ip_1, self.vlan_name_3, self.vlan_id_3, mem_2)

            vlan_detail = get_vlan(self.dut_ip_1)
            for vlan in vlan_detail or []:
                if vlan.get("vlanid") in [self.vlan_id_2, self.vlan_id_3] :
                    if vlan.get("vlanid") is self.vlan_id_2:
                        assert set(vlan.get("members")) == set(mem.keys())
                        for member_if, tagging_mode in get_vlan_members(
                            self.dut_ip_1, vlan.get("name")
                        ).items():
                            assert tagging_mode == str(mem.get(member_if))
                    elif vlan.get("vlanid") is self.vlan_id_3:
                        assert set(vlan.get("members")) == set(mem_2.keys())
                        for member_if, tagging_mode in get_vlan_members(
                            self.dut_ip_1, vlan.get("name")
                        ).items():
                            assert tagging_mode == str(mem_2.get(member_if))

        except RpcError as err:
            self.fail(err)

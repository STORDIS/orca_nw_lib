from neomodel import (
    BooleanProperty,
    ArrayProperty,
    StructuredNode,
    StructuredRel,
    StringProperty,
    IntegerProperty,
    RelationshipTo,
    JSONProperty,
)


class Device(StructuredNode):
    """
    Represents a device in the database.
    """

    img_name = StringProperty()
    mgt_intf = StringProperty()
    mgt_ip = StringProperty(required=True)
    hwsku = StringProperty()
    mac = StringProperty(unique_index=True)
    platform = StringProperty()
    type = StringProperty()

    system_status = StringProperty()
    image_list = ArrayProperty()

    neighbor = RelationshipTo("Device", "LLDP")
    interfaces = RelationshipTo("Interface", "HAS")
    port_chnl = RelationshipTo("PortChannel", "HAS")
    mclags = RelationshipTo("MCLAG", "HAS")
    port_groups = RelationshipTo("PortGroup", "HAS")
    bgp = RelationshipTo("BGP", "BGP_GLOBAL")
    vlans = RelationshipTo("Vlan", "HAS")
    mclag_gw_macs = RelationshipTo("MCLAG_GW_MAC", "HAS")

    bgp_neighbor = RelationshipTo("BGP_NEIGHBOR", "HAS")

    stp_global = RelationshipTo("STP_GLOBAL", "HAS")
    stp_port = RelationshipTo("STP_PORT", "HAS")
    stp_vlan = RelationshipTo("STP_VLAN", "HAS")

    def copy_properties(self, other):
        """
        Copy properties from another Device object to this object.
        """
        self.img_name = other.img_name
        self.mgt_intf = other.mgt_intf
        self.mgt_ip = other.mgt_ip
        self.hwsku = other.hwsku
        self.mac = other.mac
        self.platform = other.platform
        self.type = other.type
        self.system_status = other.system_status
        self.image_list = other.image_list

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.mgt_ip == other.mgt_ip and self.mac == other.mac
        return NotImplemented

    def __hash__(self):
        return hash((self.mgt_ip, self.mac))

    def __str__(self) -> str:
        """
        Return the management IP address as a string representation of the object.
        """
        return str(self.mgt_ip)


class PortChannel(StructuredNode):
    """
    Represents a port channel in the database.
    """

    lag_name = StringProperty(unique_index=True)  # name of port channel
    active = BooleanProperty()
    admin_sts = StringProperty()
    mtu = IntegerProperty()
    name = StringProperty()  # name of protocol e.g. lacp
    fallback_operational = BooleanProperty()
    oper_sts = StringProperty()
    speed = StringProperty()
    oper_sts_reason = StringProperty()
    static = BooleanProperty()
    fallback = BooleanProperty()
    fast_rate = BooleanProperty()
    min_links = IntegerProperty()
    description = StringProperty()
    graceful_shutdown_mode = StringProperty()
    ip_address = StringProperty()
    vlan_members = JSONProperty()

    members = RelationshipTo("Interface", "HAS_MEMBER")
    peer_link = RelationshipTo("PortChannel", "peer_link")

    stp_port = RelationshipTo("STP_PORT", "HAS")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.lag_name == other.lag_name
        return NotImplemented

    def __hash__(self):
        return hash(self.lag_name)

    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        """
        return str(self.lag_name)


class MCLAG_GW_MAC(StructuredNode):
    """
    Represents a MCLAG gateway MAC address in the database.
    """

    gateway_mac = StringProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.gateway_mac == other.gateway_mac
        return NotImplemented

    def __hash__(self):
        return hash(self.gateway_mac)

    def __str__(self):
        return str(self.gateway_mac)


class MCLAG(StructuredNode):
    """
    Represents a MCLAG in the database.
    """

    domain_id = IntegerProperty()
    keepalive_interval = IntegerProperty()
    mclag_sys_mac = StringProperty()
    peer_addr = StringProperty()
    peer_link = StringProperty()
    session_timeout = IntegerProperty()
    source_address = StringProperty()
    oper_status = StringProperty()
    role = StringProperty()
    system_mac = StringProperty()
    delay_restore = IntegerProperty()
    session_vrf = StringProperty()
    fast_convergence = StringProperty()

    intfc_members = RelationshipTo("Interface", "MEM_IF")
    portChnl_member = RelationshipTo("PortChannel", "MEM_CHNL")
    peer_link_node = RelationshipTo("PortChannel", "PEER_LINK")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.domain_id == other.domain_id
        return NotImplemented

    def __hash__(self):
        return hash(self.domain_id)

    def __str__(self):
        return str(self.domain_id)


class SubInterface(StructuredNode):
    """
    Represents a sub interface in the database.
    """

    ip_address = StringProperty()
    secondary = BooleanProperty()
    prefix = IntegerProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.ip_address == other.ip_address
        return NotImplemented

    def __hash__(self):
        return hash(self.ip_address)

    def __str__(self):
        return str(self.ip_address)


class Interface(StructuredNode):
    """
    Represents an interface in the database.
    """

    name = StringProperty(unique_index=True)
    enabled = BooleanProperty()
    mtu = IntegerProperty()
    fec = StringProperty()
    speed = StringProperty()
    oper_sts = StringProperty()
    admin_sts = StringProperty()
    description = StringProperty()
    last_chng = StringProperty()
    mac_addr = StringProperty()
    subInterfaces = RelationshipTo("SubInterface", "HAS")
    lldp_neighbour = RelationshipTo("Interface", "LLDP_NBR")
    alias = StringProperty()
    lanes = StringProperty()
    valid_speeds = StringProperty()
    adv_speeds = StringProperty()
    link_training = StringProperty()
    autoneg = StringProperty()
    lldp_nbrs=JSONProperty() ## LLDP remote device in the format  - {nbr_ip:[Eth0,Eth1].........}

    breakout_mode = StringProperty()
    breakout_status = StringProperty()
    breakout_supported = BooleanProperty()

    stp_port = RelationshipTo("STP_PORT", "HAS")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return str(self.name)


class PortGroup(StructuredNode):
    """
    Represents a port group in the database.
    """

    port_group_id = StringProperty()
    speed = StringProperty()
    valid_speeds = ArrayProperty()
    default_speed = StringProperty()
    memberInterfaces = RelationshipTo("Interface", "MEMBER_IF")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.port_group_id == other.port_group_id
        return NotImplemented

    def __hash__(self):
        return hash(self.port_group_id)

    def __str__(self):
        return str(self.port_group_id)


class BGP(StructuredNode):
    """
    Represents a BGP neighbor in the database.
    """

    local_asn = IntegerProperty()
    vrf_name = StringProperty()
    router_id = StringProperty()

    af = RelationshipTo("BGP_GLOBAL_AF", "AF")
    af_network = RelationshipTo("BGP_GLOBAL_AF_NETWORK", "AF_NETWORK")
    af_aggregate_addr = RelationshipTo("BGP_GLOBAL_AF_AGGREGATE_ADDR", "AF_AGGREGATE_ADDR")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.local_asn == other.local_asn
        return NotImplemented

    def __hash__(self):
        return hash(self.local_asn)

    def __str__(self):
        return str(self.local_asn)


class BGP_GLOBAL_AF(StructuredNode):
    """
    Represents a BGP Global AF in the database.
    """

    afi_safi = StringProperty()
    vrf_name = StringProperty()
    max_ebgp_paths = IntegerProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.afi_safi == other.afi_safi
        return NotImplemented

    def __hash__(self):
        return hash(self.afi_safi)

    def __str__(self):
        return str(self.afi_safi)


class VlanMemRel(StructuredRel):
    """
    Represents a relationship between a VLAN and an interface.
    """

    tagging_mode = StringProperty()


class Vlan(StructuredNode):
    """
    Represents a VLAN in the database.
    """

    vlanid = IntegerProperty()
    name = StringProperty()
    mtu = IntegerProperty()
    oper_status = StringProperty()
    autostate = StringProperty()
    ip_address = StringProperty()
    sag_ip_address = ArrayProperty()
    enabled = BooleanProperty()
    description = StringProperty()

    memberInterfaces = RelationshipTo("Interface", "MEMBER_IF", model=VlanMemRel)
    memberPortChannel = RelationshipTo("PortChannel", "MEMBER_PORT_CHANNEL", model=VlanMemRel)

    stp_vlan = RelationshipTo("STP_VLAN", "HAS")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.vlanid == other.vlanid
        return NotImplemented

    def __hash__(self):
        return hash(self.vlanid)

    def __str__(self):
        return str(self.vlanid)


class STP_GLOBAL(StructuredNode):
    """
    Represents a STP Global in the database.
    """

    device_ip = StringProperty()
    enabled_protocol = ArrayProperty()
    bpdu_filter = BooleanProperty()
    loop_guard = BooleanProperty()
    rootguard_timeout = IntegerProperty()
    portfast = BooleanProperty()
    max_age = IntegerProperty()
    hello_time = IntegerProperty()
    forwarding_delay = IntegerProperty()
    bridge_priority = IntegerProperty()
    disabled_vlans = ArrayProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.device_ip == other.device_ip
        return NotImplemented

    def __hash__(self):
        return hash(self.device_ip)

    def __str__(self):
        return str(self.device_ip)


class STP_VLAN(StructuredNode):
    """
    Represents STP VLAN in the database.
    """

    vlan_id = IntegerProperty()
    max_age = IntegerProperty()
    hello_time = IntegerProperty()
    forwarding_delay = IntegerProperty()
    bridge_priority = IntegerProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.vlan_id == other.vlan_id
        return NotImplemented

    def __hash__(self):
        return hash(self.vlan_id)

    def __str__(self):
        return str(self.vlan_id)


class STP_PORT(StructuredNode):
    """
    Represents a STP Port in the database.
    """

    if_name = StringProperty()
    edge_port = StringProperty()
    link_type = StringProperty()
    guard = StringProperty()
    bpdu_guard = BooleanProperty()
    bpdu_filter = BooleanProperty()
    portfast = BooleanProperty()
    uplink_fast = BooleanProperty()
    bpdu_guard_port_shutdown = BooleanProperty()
    cost = IntegerProperty()
    port_priority = IntegerProperty()
    stp_enabled = BooleanProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.if_name == other.if_name
        return NotImplemented

    def __hash__(self):
        return hash(self.if_name)

    def __str__(self):
        return str(self.if_name)


class BGP_GLOBAL_AF_NETWORK(StructuredNode):
    """
    Represents a BGP Global AF in the database.
    """

    afi_safi = StringProperty()
    vrf_name = StringProperty()
    ip_prefix = StringProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.afi_safi == other.afi_safi
        return NotImplemented

    def __hash__(self):
        return hash(self.afi_safi)

    def __str__(self):
        return str(self.afi_safi)


class BGP_GLOBAL_AF_AGGREGATE_ADDR(StructuredNode):
    """
    Represents a BGP Global AF in the database.
    """

    afi_safi = StringProperty()
    vrf_name = StringProperty()
    ip_prefix = StringProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.afi_safi == other.afi_safi
        return NotImplemented

    def __hash__(self):
        return hash(self.afi_safi)

    def __str__(self):
        return str(self.afi_safi)


class BGP_NEIGHBOR(StructuredNode):
    """
    Represents a BGP Neighbor in the database.
    """

    local_asn = IntegerProperty()
    remote_asn = IntegerProperty()
    neighbor_ip = StringProperty()
    vrf_name = StringProperty()
    admin_status = StringProperty()
    ebgp_multihop = BooleanProperty()
    ebgp_multihop_ttl = IntegerProperty()
    enforce_multihop = BooleanProperty()
    auth_password = StringProperty()

    remote_asn_rel = RelationshipTo("BGP", "ASN")
    local_asn_rel = RelationshipTo("BGP", "LOCAL_ASN")
    neighbor_rel = RelationshipTo("SubInterface", "BGP_NEIGHBOR")

    af = RelationshipTo("BGP_NEIGHBOR_AF", "BGP_NEIGHBOR_AF")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.neighbor_ip == other.neighbor_ip
        return NotImplemented

    def __hash__(self):
        return hash(self.neighbor_ip)

    def __str__(self):
        return str(self.neighbor_ip)


class BGP_NEIGHBOR_AF(StructuredNode):
    """
    Represents a BGP Neighbor AF in the database.
    """

    afi_safi = StringProperty()
    vrf_name = StringProperty()
    admin_status = StringProperty()
    send_community = StringProperty()
    neighbor_ip = StringProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.afi_safi == other.afi_safi
        return NotImplemented

    def __hash__(self):
        return hash(self.afi_safi)

    def __str__(self):
        return str(self.afi_safi)

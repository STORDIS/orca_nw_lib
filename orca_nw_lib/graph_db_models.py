from neomodel import BooleanProperty, ArrayProperty, StructuredNode, StringProperty, IntegerProperty,  RelationshipTo, Relationship


class Device(StructuredNode):

    img_name = StringProperty()
    mgt_intf = StringProperty()
    mgt_ip = StringProperty()
    hwsku = StringProperty()
    mac = StringProperty(unique_index=True)
    platform = StringProperty()
    type = StringProperty()

    neighbor = RelationshipTo('Device', 'LLDP')
    interfaces = RelationshipTo('Interface', 'HAS')
    port_chnl = RelationshipTo('PortChannel', 'HAS')
    mclags = RelationshipTo('MCLAG', 'HAS')
    port_groups = RelationshipTo('PortGroup', 'HAS')
    bgp = RelationshipTo('BGP', 'BGP_GLOBAL')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.mgt_ip == other.mgt_ip and self.mac == other.mac
        return NotImplemented

    def __hash__(self):
        return hash((self.mgt_ip, self.mac))

    def __str__(self):
        return self.mgt_ip


class PortChannel(StructuredNode):

    lag_name = StringProperty(unique_index=True)  # name of port channel
    active = BooleanProperty()
    admin_sts = StringProperty()
    mtu = IntegerProperty()
    name = StringProperty()  # name of protocol e.g. lacp
    fallback_operational = BooleanProperty()
    oper_sts = StringProperty()
    speed = StringProperty()
    oper_sts_reason = StringProperty()

    members = RelationshipTo('Interface', 'HAS MEMBER')
    peer_link = RelationshipTo('PortChannel', 'peer_link')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.lag_name == other.lag_name
        return NotImplemented

    def __hash__(self):
        return hash(self.lag_name)

    def __str__(self):
        return self.lag_name


class MCLAG(StructuredNode):

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
    gateway_macs = ArrayProperty()
    delay_restore = IntegerProperty()

    intfc_members = RelationshipTo('Interface', 'HAS MEMBER')
    portChnl_member = RelationshipTo('PortChannel', 'HAS MEMBER')
    peer_link_node = RelationshipTo('PortChannel', 'PEER_LINK')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.domain_id == other.domain_id
        return NotImplemented

    def __hash__(self):
        return hash(self.domain_id)

    def __str__(self):
        return str(self.domain_id)


class SubInterface(StructuredNode):
    ip_address = StringProperty()
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.local_asn == other.ip_address
        return NotImplemented

    def __hash__(self):
        return hash(self.ip_address)

    def __str__(self):
        return self.ip_address


class Interface(StructuredNode):

    name = StringProperty(unique_index=True)
    enabled = BooleanProperty()
    mtu = IntegerProperty()
    fec = BooleanProperty()
    speed = StringProperty()
    oper_sts = StringProperty()
    admin_sts = StringProperty()
    description = StringProperty()
    last_chng = StringProperty()
    mac_addr = StringProperty()
    subInterfaces = RelationshipTo('SubInterface', 'HAS')
    lldp_neighbour = RelationshipTo('Interface', 'LLDP_NBR')

    # counters
    in_bits_per_second = in_broadcast_pkts = in_discards = in_errors = in_multicast_pkts = in_octets =\
        in_octets_per_second = in_pkts = in_pkts_per_second = in_unicast_pkts = in_utilization = last_clear =\
        out_bits_per_second = out_broadcast_pkts = out_discards = out_errors = out_multicast_pkts = out_octets =\
        out_octets_per_second = out_pkts = out_pkts_per_second = out_unicast_pkts = out_utilization = StringProperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class PortGroup(StructuredNode):

    port_group_id = IntegerProperty()
    speed = StringProperty()
    valid_speeds = ArrayProperty()
    default_speed = StringProperty()
    memberInterfaces = RelationshipTo('Interface', 'MEMBER')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.port_group_id == other.port_group_id
        return NotImplemented

    def __hash__(self):
        return hash(self.port_group_id)

    def __str__(self):
        return self.port_group_id


class BGP(StructuredNode):
    local_asn = IntegerProperty()
    vrf_name = StringProperty()
    router_id = StringProperty()
    remote_asn = ArrayProperty()
    nbr_ips=ArrayProperty()
    
    neighbors = RelationshipTo('SubInterface', 'BGP_NEIGHBOR')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.local_asn == other.local_asn
        return NotImplemented

    def __hash__(self):
        return hash(self.local_asn)

    def __str__(self):
        return str(self.local_asn)

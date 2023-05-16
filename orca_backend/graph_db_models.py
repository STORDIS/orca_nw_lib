from neomodel import BooleanProperty,ArrayProperty,StructuredNode, StringProperty, IntegerProperty,  UniqueIdProperty, RelationshipTo


class Device(StructuredNode):
    
    img_name=StringProperty()
    mgt_intf=StringProperty()
    mgt_ip=StringProperty()
    hwsku=StringProperty()
    mac=StringProperty(unique_index=True)
    platform=StringProperty()
    type=StringProperty()
    
    neighbor=RelationshipTo('Device','LLDP')
    interfaces=RelationshipTo('Interface','HAS')
    port_chnl=RelationshipTo('PortChannel','HAS')
    mclags=RelationshipTo('MCLAG','HAS')
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.mgt_ip == other.mgt_ip and self.mac == other.mac
        return NotImplemented
    
    def __hash__(self):
        return hash((self.mgt_ip, self.mac))
    
    def __str__(self):
        return self.mgt_ip
    
class Interface(StructuredNode):
    
    name=StringProperty(unique_index=True)
    enabled=BooleanProperty()
    mtu=IntegerProperty()
    fec=BooleanProperty()
    speed=StringProperty()
    oper_sts=StringProperty()
    admin_sts=StringProperty()
    description=StringProperty()
    last_chng=StringProperty()
    mac_addr=StringProperty()
       
    ##counters
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
    
class PortChannel(StructuredNode):
    
    lag_name=StringProperty(unique_index=True)
    active=BooleanProperty()
    admin_sts=StringProperty()
    mtu=IntegerProperty()
    name=StringProperty()
    fallback_operational=BooleanProperty()
    oper_sts=StringProperty()
    speed=StringProperty()
    oper_sts_reason=StringProperty()
    
    members=RelationshipTo('Interface','HAS MEMBER')
       
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.lag_name == other.lag_name
        return NotImplemented
    
    def __hash__(self):
        return hash(self.lag_name)
    
    def __str__(self):
        return self.lag_name
    
    
class MCLAG(StructuredNode):
    
    domain_id=IntegerProperty()
    keepalive_interval=IntegerProperty()
    mclag_sys_mac=StringProperty()
    peer_addr=StringProperty()
    peer_link=StringProperty()
    session_timeout=IntegerProperty()
    source_address=StringProperty()
    oper_status=StringProperty()
    role=StringProperty()
    system_mac=StringProperty()
    gateway_macs=ArrayProperty()
    
    intfc_members=RelationshipTo('Interface','HAS MEMBER')
    portChnl_member=RelationshipTo('PortChannel','HAS MEMBER')
       
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.domain_id == other.domain_id
        return NotImplemented
    
    def __hash__(self):
        return hash(self.domain_id)
    
    def __str__(self):
        return self.domain_id
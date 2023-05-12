from neomodel import Relationship,StructuredNode, StringProperty, IntegerProperty,  UniqueIdProperty, RelationshipTo


class Device(StructuredNode):
    
    img_name=StringProperty()
    mgt_intf=StringProperty()
    mgt_ip=StringProperty()
    hwsku=StringProperty()
    mac=StringProperty(unique_index=True)
    platform=StringProperty()
    type=StringProperty()
    
    neighbor=RelationshipTo('Device','LLDP')
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.mgt_ip == other.mgt_ip and self.mac == other.mac
        return NotImplemented
    
    def __hash__(self):
        return hash((self.mgt_ip, self.mac))
    
    def __str__(self):
        return self.mgt_ip
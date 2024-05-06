from enum import Enum, auto


class Speed(Enum):
    SPEED_1GB = auto()
    SPEED_5GB = auto()
    SPEED_10GB = auto()
    SPEED_25GB = auto()
    SPEED_40GB = auto()
    SPEED_50GB = auto()
    SPEED_100GB = auto()

    def get_oc_val(self):
        return f"openconfig-if-ethernet:{self.name}"

    @staticmethod
    def get_enum_from_str(name: str):
        return Speed[name] if name in Speed.__members__ else None

    @staticmethod
    def getSpeedStrFromOCStr(oc_str):
        return oc_str.split(":")[1]

    def __str__(self) -> str:
        return self.name


class PortFec(Enum):
    FEC_RS = auto()
    FEC_FC = auto()
    FEC_DISABLED = auto()
    FEC_AUTO = auto()

    def get_oc_val(self):
        return f"openconfig-platform-types:{self.name}"

    @staticmethod
    def get_enum_from_str(name: str):
        return PortFec[name] if name in PortFec.__members__ else None

    @staticmethod
    def getFecStrFromOCStr(oc_str):
        return oc_str.split(":")[1] if oc_str else None

    def __str__(self) -> str:
        return self.name


class VlanTagMode(str, Enum):
    tagged = auto()
    untagged = auto()


    @staticmethod
    def get_enum_from_str(name: str):
        return VlanTagMode[name] if name in VlanTagMode.__members__ else None
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


class IFMode(str, Enum):
    TRUNK = auto()
    ACCESS = auto()


    @staticmethod
    def get_enum_from_str(name: str):
        return IFMode[name] if name in IFMode.__members__ else None
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

class VlanAutoState(str, Enum):
    enable = auto()
    disable = auto()


    @staticmethod
    def get_enum_from_str(name: str):
        return VlanAutoState[name] if name in VlanAutoState.__members__ else None
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
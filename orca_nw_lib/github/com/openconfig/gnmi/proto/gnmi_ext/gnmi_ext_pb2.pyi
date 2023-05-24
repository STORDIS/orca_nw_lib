from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
EID_EXPERIMENTAL: ExtensionID
EID_UNSET: ExtensionID

class Extension(_message.Message):
    __slots__ = ["history", "master_arbitration", "registered_ext"]
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    MASTER_ARBITRATION_FIELD_NUMBER: _ClassVar[int]
    REGISTERED_EXT_FIELD_NUMBER: _ClassVar[int]
    history: History
    master_arbitration: MasterArbitration
    registered_ext: RegisteredExtension
    def __init__(self, registered_ext: _Optional[_Union[RegisteredExtension, _Mapping]] = ..., master_arbitration: _Optional[_Union[MasterArbitration, _Mapping]] = ..., history: _Optional[_Union[History, _Mapping]] = ...) -> None: ...

class History(_message.Message):
    __slots__ = ["range", "snapshot_time"]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_TIME_FIELD_NUMBER: _ClassVar[int]
    range: TimeRange
    snapshot_time: int
    def __init__(self, snapshot_time: _Optional[int] = ..., range: _Optional[_Union[TimeRange, _Mapping]] = ...) -> None: ...

class MasterArbitration(_message.Message):
    __slots__ = ["election_id", "role"]
    ELECTION_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    election_id: Uint128
    role: Role
    def __init__(self, role: _Optional[_Union[Role, _Mapping]] = ..., election_id: _Optional[_Union[Uint128, _Mapping]] = ...) -> None: ...

class RegisteredExtension(_message.Message):
    __slots__ = ["id", "msg"]
    ID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    id: ExtensionID
    msg: bytes
    def __init__(self, id: _Optional[_Union[ExtensionID, str]] = ..., msg: _Optional[bytes] = ...) -> None: ...

class Role(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class TimeRange(_message.Message):
    __slots__ = ["end", "start"]
    END_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    end: int
    start: int
    def __init__(self, start: _Optional[int] = ..., end: _Optional[int] = ...) -> None: ...

class Uint128(_message.Message):
    __slots__ = ["high", "low"]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    LOW_FIELD_NUMBER: _ClassVar[int]
    high: int
    low: int
    def __init__(self, high: _Optional[int] = ..., low: _Optional[int] = ...) -> None: ...

class ExtensionID(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

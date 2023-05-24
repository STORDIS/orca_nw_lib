from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from github.com.openconfig.gnmi.proto.gnmi_ext import gnmi_ext_pb2 as _gnmi_ext_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

ASCII: Encoding
BYTES: Encoding
DESCRIPTOR: _descriptor.FileDescriptor
GNMI_SERVICE_FIELD_NUMBER: _ClassVar[int]
JSON: Encoding
JSON_IETF: Encoding
ON_CHANGE: SubscriptionMode
PROTO: Encoding
SAMPLE: SubscriptionMode
TARGET_DEFINED: SubscriptionMode
gnmi_service: _descriptor.FieldDescriptor

class CapabilityRequest(_message.Message):
    __slots__ = ["extension"]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    def __init__(self, extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class CapabilityResponse(_message.Message):
    __slots__ = ["extension", "gNMI_version", "supported_encodings", "supported_models"]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    GNMI_VERSION_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_ENCODINGS_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_MODELS_FIELD_NUMBER: _ClassVar[int]
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    gNMI_version: str
    supported_encodings: _containers.RepeatedScalarFieldContainer[Encoding]
    supported_models: _containers.RepeatedCompositeFieldContainer[ModelData]
    def __init__(self, supported_models: _Optional[_Iterable[_Union[ModelData, _Mapping]]] = ..., supported_encodings: _Optional[_Iterable[_Union[Encoding, str]]] = ..., gNMI_version: _Optional[str] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class Decimal64(_message.Message):
    __slots__ = ["digits", "precision"]
    DIGITS_FIELD_NUMBER: _ClassVar[int]
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    digits: int
    precision: int
    def __init__(self, digits: _Optional[int] = ..., precision: _Optional[int] = ...) -> None: ...

class Error(_message.Message):
    __slots__ = ["code", "data", "message"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    data: _any_pb2.Any
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., data: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ["encoding", "extension", "path", "prefix", "type", "use_models"]
    class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ALL: GetRequest.DataType
    CONFIG: GetRequest.DataType
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    OPERATIONAL: GetRequest.DataType
    PATH_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    STATE: GetRequest.DataType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USE_MODELS_FIELD_NUMBER: _ClassVar[int]
    encoding: Encoding
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    path: _containers.RepeatedCompositeFieldContainer[Path]
    prefix: Path
    type: GetRequest.DataType
    use_models: _containers.RepeatedCompositeFieldContainer[ModelData]
    def __init__(self, prefix: _Optional[_Union[Path, _Mapping]] = ..., path: _Optional[_Iterable[_Union[Path, _Mapping]]] = ..., type: _Optional[_Union[GetRequest.DataType, str]] = ..., encoding: _Optional[_Union[Encoding, str]] = ..., use_models: _Optional[_Iterable[_Union[ModelData, _Mapping]]] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ["error", "extension", "notification"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_FIELD_NUMBER: _ClassVar[int]
    error: Error
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    notification: _containers.RepeatedCompositeFieldContainer[Notification]
    def __init__(self, notification: _Optional[_Iterable[_Union[Notification, _Mapping]]] = ..., error: _Optional[_Union[Error, _Mapping]] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class ModelData(_message.Message):
    __slots__ = ["name", "organization", "version"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    name: str
    organization: str
    version: str
    def __init__(self, name: _Optional[str] = ..., organization: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...

class Notification(_message.Message):
    __slots__ = ["atomic", "delete", "prefix", "timestamp", "update"]
    ATOMIC_FIELD_NUMBER: _ClassVar[int]
    DELETE_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    atomic: bool
    delete: _containers.RepeatedCompositeFieldContainer[Path]
    prefix: Path
    timestamp: int
    update: _containers.RepeatedCompositeFieldContainer[Update]
    def __init__(self, timestamp: _Optional[int] = ..., prefix: _Optional[_Union[Path, _Mapping]] = ..., update: _Optional[_Iterable[_Union[Update, _Mapping]]] = ..., delete: _Optional[_Iterable[_Union[Path, _Mapping]]] = ..., atomic: bool = ...) -> None: ...

class Path(_message.Message):
    __slots__ = ["elem", "element", "origin", "target"]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    ELEM_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    elem: _containers.RepeatedCompositeFieldContainer[PathElem]
    element: _containers.RepeatedScalarFieldContainer[str]
    origin: str
    target: str
    def __init__(self, element: _Optional[_Iterable[str]] = ..., origin: _Optional[str] = ..., elem: _Optional[_Iterable[_Union[PathElem, _Mapping]]] = ..., target: _Optional[str] = ...) -> None: ...

class PathElem(_message.Message):
    __slots__ = ["key", "name"]
    class KeyEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KEY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    key: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., key: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Poll(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class QOSMarking(_message.Message):
    __slots__ = ["marking"]
    MARKING_FIELD_NUMBER: _ClassVar[int]
    marking: int
    def __init__(self, marking: _Optional[int] = ...) -> None: ...

class ScalarArray(_message.Message):
    __slots__ = ["element"]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    element: _containers.RepeatedCompositeFieldContainer[TypedValue]
    def __init__(self, element: _Optional[_Iterable[_Union[TypedValue, _Mapping]]] = ...) -> None: ...

class SetRequest(_message.Message):
    __slots__ = ["delete", "extension", "prefix", "replace", "update"]
    DELETE_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    REPLACE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    delete: _containers.RepeatedCompositeFieldContainer[Path]
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    prefix: Path
    replace: _containers.RepeatedCompositeFieldContainer[Update]
    update: _containers.RepeatedCompositeFieldContainer[Update]
    def __init__(self, prefix: _Optional[_Union[Path, _Mapping]] = ..., delete: _Optional[_Iterable[_Union[Path, _Mapping]]] = ..., replace: _Optional[_Iterable[_Union[Update, _Mapping]]] = ..., update: _Optional[_Iterable[_Union[Update, _Mapping]]] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class SetResponse(_message.Message):
    __slots__ = ["extension", "message", "prefix", "response", "timestamp"]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    message: Error
    prefix: Path
    response: _containers.RepeatedCompositeFieldContainer[UpdateResult]
    timestamp: int
    def __init__(self, prefix: _Optional[_Union[Path, _Mapping]] = ..., response: _Optional[_Iterable[_Union[UpdateResult, _Mapping]]] = ..., message: _Optional[_Union[Error, _Mapping]] = ..., timestamp: _Optional[int] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class SubscribeRequest(_message.Message):
    __slots__ = ["extension", "poll", "subscribe"]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    POLL_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    poll: Poll
    subscribe: SubscriptionList
    def __init__(self, subscribe: _Optional[_Union[SubscriptionList, _Mapping]] = ..., poll: _Optional[_Union[Poll, _Mapping]] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class SubscribeResponse(_message.Message):
    __slots__ = ["error", "extension", "sync_response", "update"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    SYNC_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    error: Error
    extension: _containers.RepeatedCompositeFieldContainer[_gnmi_ext_pb2.Extension]
    sync_response: bool
    update: Notification
    def __init__(self, update: _Optional[_Union[Notification, _Mapping]] = ..., sync_response: bool = ..., error: _Optional[_Union[Error, _Mapping]] = ..., extension: _Optional[_Iterable[_Union[_gnmi_ext_pb2.Extension, _Mapping]]] = ...) -> None: ...

class Subscription(_message.Message):
    __slots__ = ["heartbeat_interval", "mode", "path", "sample_interval", "suppress_redundant"]
    HEARTBEAT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    SUPPRESS_REDUNDANT_FIELD_NUMBER: _ClassVar[int]
    heartbeat_interval: int
    mode: SubscriptionMode
    path: Path
    sample_interval: int
    suppress_redundant: bool
    def __init__(self, path: _Optional[_Union[Path, _Mapping]] = ..., mode: _Optional[_Union[SubscriptionMode, str]] = ..., sample_interval: _Optional[int] = ..., suppress_redundant: bool = ..., heartbeat_interval: _Optional[int] = ...) -> None: ...

class SubscriptionList(_message.Message):
    __slots__ = ["allow_aggregation", "encoding", "mode", "prefix", "qos", "subscription", "updates_only", "use_models"]
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ALLOW_AGGREGATION_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    ONCE: SubscriptionList.Mode
    POLL: SubscriptionList.Mode
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    QOS_FIELD_NUMBER: _ClassVar[int]
    STREAM: SubscriptionList.Mode
    SUBSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    UPDATES_ONLY_FIELD_NUMBER: _ClassVar[int]
    USE_MODELS_FIELD_NUMBER: _ClassVar[int]
    allow_aggregation: bool
    encoding: Encoding
    mode: SubscriptionList.Mode
    prefix: Path
    qos: QOSMarking
    subscription: _containers.RepeatedCompositeFieldContainer[Subscription]
    updates_only: bool
    use_models: _containers.RepeatedCompositeFieldContainer[ModelData]
    def __init__(self, prefix: _Optional[_Union[Path, _Mapping]] = ..., subscription: _Optional[_Iterable[_Union[Subscription, _Mapping]]] = ..., qos: _Optional[_Union[QOSMarking, _Mapping]] = ..., mode: _Optional[_Union[SubscriptionList.Mode, str]] = ..., allow_aggregation: bool = ..., use_models: _Optional[_Iterable[_Union[ModelData, _Mapping]]] = ..., encoding: _Optional[_Union[Encoding, str]] = ..., updates_only: bool = ...) -> None: ...

class TypedValue(_message.Message):
    __slots__ = ["any_val", "ascii_val", "bool_val", "bytes_val", "decimal_val", "double_val", "float_val", "int_val", "json_ietf_val", "json_val", "leaflist_val", "proto_bytes", "string_val", "uint_val"]
    ANY_VAL_FIELD_NUMBER: _ClassVar[int]
    ASCII_VAL_FIELD_NUMBER: _ClassVar[int]
    BOOL_VAL_FIELD_NUMBER: _ClassVar[int]
    BYTES_VAL_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_VAL_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VAL_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VAL_FIELD_NUMBER: _ClassVar[int]
    INT_VAL_FIELD_NUMBER: _ClassVar[int]
    JSON_IETF_VAL_FIELD_NUMBER: _ClassVar[int]
    JSON_VAL_FIELD_NUMBER: _ClassVar[int]
    LEAFLIST_VAL_FIELD_NUMBER: _ClassVar[int]
    PROTO_BYTES_FIELD_NUMBER: _ClassVar[int]
    STRING_VAL_FIELD_NUMBER: _ClassVar[int]
    UINT_VAL_FIELD_NUMBER: _ClassVar[int]
    any_val: _any_pb2.Any
    ascii_val: str
    bool_val: bool
    bytes_val: bytes
    decimal_val: Decimal64
    double_val: float
    float_val: float
    int_val: int
    json_ietf_val: bytes
    json_val: bytes
    leaflist_val: ScalarArray
    proto_bytes: bytes
    string_val: str
    uint_val: int
    def __init__(self, string_val: _Optional[str] = ..., int_val: _Optional[int] = ..., uint_val: _Optional[int] = ..., bool_val: bool = ..., bytes_val: _Optional[bytes] = ..., float_val: _Optional[float] = ..., double_val: _Optional[float] = ..., decimal_val: _Optional[_Union[Decimal64, _Mapping]] = ..., leaflist_val: _Optional[_Union[ScalarArray, _Mapping]] = ..., any_val: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., json_val: _Optional[bytes] = ..., json_ietf_val: _Optional[bytes] = ..., ascii_val: _Optional[str] = ..., proto_bytes: _Optional[bytes] = ...) -> None: ...

class Update(_message.Message):
    __slots__ = ["duplicates", "path", "val", "value"]
    DUPLICATES_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    VAL_FIELD_NUMBER: _ClassVar[int]
    duplicates: int
    path: Path
    val: TypedValue
    value: Value
    def __init__(self, path: _Optional[_Union[Path, _Mapping]] = ..., value: _Optional[_Union[Value, _Mapping]] = ..., val: _Optional[_Union[TypedValue, _Mapping]] = ..., duplicates: _Optional[int] = ...) -> None: ...

class UpdateResult(_message.Message):
    __slots__ = ["message", "op", "path", "timestamp"]
    class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DELETE: UpdateResult.Operation
    INVALID: UpdateResult.Operation
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    REPLACE: UpdateResult.Operation
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    UPDATE: UpdateResult.Operation
    message: Error
    op: UpdateResult.Operation
    path: Path
    timestamp: int
    def __init__(self, timestamp: _Optional[int] = ..., path: _Optional[_Union[Path, _Mapping]] = ..., message: _Optional[_Union[Error, _Mapping]] = ..., op: _Optional[_Union[UpdateResult.Operation, str]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ["type", "value"]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: Encoding
    value: bytes
    def __init__(self, value: _Optional[bytes] = ..., type: _Optional[_Union[Encoding, str]] = ...) -> None: ...

class Encoding(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class SubscriptionMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

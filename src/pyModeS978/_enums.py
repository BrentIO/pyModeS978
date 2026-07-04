from enum import IntEnum


class AddressQualifier(IntEnum):
    ADSB_ICAO = 0
    NATIONAL_RESERVED = 1
    TISB_ICAO = 2
    TISB_OTHER = 3
    VEHICLE = 4
    FIXED_BEACON = 5
    RESERVED_6 = 6
    RESERVED_7 = 7


class PayloadType(IntEnum):
    SHORT = 0
    LONG = 1
    SHORT_AUX = 2
    SHORT_MS = 3


def coerce(enum_cls: type[IntEnum], value: int) -> IntEnum | int:
    """`enum_cls(value)`, but falls back to the plain int for values with no named member."""
    try:
        return enum_cls(value)
    except ValueError:
        return value

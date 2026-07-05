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


_EMITTER_CATEGORY_NAMES = [
    "NO_INFORMATION",
    "LIGHT",
    "MEDIUM",
    "MEDIUM_LARGE",
    "MEDIUM_LARGE_HIGH_VORTEX",
    "HEAVY",
    "HIGHLY_MANEUVERABLE",
    "ROTORCRAFT",
    "RESERVED_8",
    "GLIDER_SAILPLANE",
    "LIGHTER_THAN_AIR",
    "PARACHUTIST_SKYDIVER",
    "ULTRALIGHT_HANGGLIDER_PARAGLIDER",
    "RESERVED_13",
    "UAV",
    "SPACE_TRANSATMOSPHERIC",
    "RESERVED_16",
    "EMERGENCY_VEHICLE",
    "SERVICE_VEHICLE",
    "POINT_OBSTACLE",
    "CLUSTER_OBSTACLE",
    "LINE_OBSTACLE",
] + [f"RESERVED_{i}" for i in range(22, 40)]

EmitterCategory = IntEnum("EmitterCategory", _EMITTER_CATEGORY_NAMES, start=0)


class Emergency(IntEnum):
    NO_EMERGENCY = 0
    GENERAL = 1
    MEDICAL = 2
    MINIMUM_FUEL = 3
    NO_COMMUNICATIONS = 4
    UNLAWFUL_INTERFERENCE = 5
    DOWNED_AIRCRAFT = 6
    RESERVED_7 = 7


class SILSupplement(IntEnum):
    PER_HOUR = 0
    PER_SAMPLE = 1


class AirgroundState(IntEnum):
    AIRBORNE_SUBSONIC = 0
    AIRBORNE_SUPERSONIC = 1
    ON_GROUND = 2
    RESERVED = 3


class AltitudeSource(IntEnum):
    BARO = 0
    GNSS = 1


class HeadingType(IntEnum):
    MAGNETIC = 2
    TRUE = 3


def coerce(enum_cls: type[IntEnum], value: int) -> IntEnum | int:
    """`enum_cls(value)`, but falls back to the plain int for values with no named member."""
    try:
        return enum_cls(value)
    except ValueError:
        return value

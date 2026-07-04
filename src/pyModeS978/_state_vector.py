import math

from ._bits import read_uint
from ._enums import AddressQualifier

# ADS-B aircraft length/width code table (DO-260/DO-282), meters.
_DIMENSIONS_WIDTHS_M = [
    11.5, 23, 28.5, 34, 33, 38, 39.5, 45, 45, 52, 59.5, 67, 72.5, 80, 80, 90,
]

_AIRGROUND_STRINGS = {0: "airborne", 1: "airborne", 2: "ground", 3: "reserved"}
_TRACK_TYPES = {1: "track", 2: "magnetic_heading", 3: "true_heading"}
_TISB_ADDRESS_QUALIFIERS = {2, 3}


def decode(payload: bytes, address_qualifier: AddressQualifier | int) -> dict:
    nic = read_uint(payload, 92, 4)
    raw_lat = read_uint(payload, 32, 23)
    raw_lon = read_uint(payload, 55, 24)

    latitude = longitude = None
    if nic != 0 or raw_lat != 0 or raw_lon != 0:
        latitude = raw_lat * 360 / 2**24
        if latitude > 90:
            latitude -= 180
        longitude = raw_lon * 360 / 2**24
        if longitude > 180:
            longitude -= 360

    raw_alt = read_uint(payload, 80, 12)
    altitude = altitude_type = None
    if raw_alt != 0:
        altitude = (raw_alt - 1) * 25 - 1000
        altitude_type = "geo" if read_uint(payload, 79, 1) else "baro"

    raw_airground = read_uint(payload, 96, 2)
    airground_state = _AIRGROUND_STRINGS[raw_airground]

    groundspeed = track = track_type = None
    vertical_rate = vertical_rate_source = None
    length = width = position_offset = None

    if raw_airground in (0, 1):
        groundspeed, track, track_type = _decode_airborne_velocity(
            payload, supersonic=raw_airground == 1
        )
        vertical_rate, vertical_rate_source = _decode_vertical_rate(payload)
    elif raw_airground == 2:
        groundspeed, track, track_type = _decode_ground_velocity(payload)
        length, width, position_offset = _decode_dimensions(payload)
    # raw_airground == 3 (reserved): no velocity/vertical-rate/dimensions defined

    utc_coupled = tisb_site_id = None
    if address_qualifier in _TISB_ADDRESS_QUALIFIERS:
        tisb_site_id = read_uint(payload, 132, 4)
    else:
        utc_coupled = bool(read_uint(payload, 132, 1))

    return {
        "latitude": latitude if latitude is None else round(latitude, 6),
        "longitude": longitude if longitude is None else round(longitude, 6),
        "altitude": altitude,
        "altitude_type": altitude_type,
        "nic": nic,
        "airground_state": airground_state,
        "groundspeed": groundspeed if groundspeed is None else round(groundspeed),
        "track": track if track is None else round(track),
        "track_type": track_type,
        "vertical_rate": vertical_rate,
        "vertical_rate_source": vertical_rate_source,
        "length": length,
        "width": width,
        "position_offset": position_offset,
        "utc_coupled": utc_coupled,
        "tisb_site_id": tisb_site_id,
    }


def _decode_signed_velocity(payload: bytes, start_bit: int, supersonic: bool) -> int | None:
    raw = read_uint(payload, start_bit, 11)
    magnitude = raw & 0x3FF
    if magnitude == 0:
        return None
    value = magnitude - 1
    if raw & 0x400:
        value = -value
    if supersonic:
        value *= 4
    return value


def _decode_airborne_velocity(payload: bytes, *, supersonic: bool):
    ns = _decode_signed_velocity(payload, 99, supersonic)
    ew = _decode_signed_velocity(payload, 110, supersonic)

    if ns is None or ew is None:
        return None, None, None

    groundspeed = math.sqrt(ns * ns + ew * ew)
    if ns == 0 and ew == 0:
        return groundspeed, None, None

    track = (360 + 90 - math.degrees(math.atan2(ns, ew))) % 360
    return groundspeed, track, "track"


def _decode_ground_velocity(payload: bytes):
    raw_gs = read_uint(payload, 99, 11)
    gs_magnitude = raw_gs & 0x3FF
    groundspeed = None if gs_magnitude == 0 else gs_magnitude - 1

    raw_track = read_uint(payload, 110, 11)
    track_type_code = (raw_track >> 9) & 0x03
    track_type = _TRACK_TYPES.get(track_type_code)
    track = None
    if track_type is not None:
        track = (raw_track & 0x1FF) * 360 / 512

    return groundspeed, track, track_type


def _decode_vertical_rate(payload: bytes):
    raw = read_uint(payload, 121, 11)
    magnitude = raw & 0x1FF
    if magnitude == 0:
        return None, None
    value = (magnitude - 1) * 64
    if raw & 0x200:
        value = -value
    source = "baro" if raw & 0x400 else "geo"
    return value, source


def _decode_dimensions(payload: bytes):
    width_code = read_uint(payload, 121, 4)
    length_code = width_code & 0x07
    length = 15 + 10 * length_code
    width = _DIMENSIONS_WIDTHS_M[width_code]
    position_offset = bool(read_uint(payload, 125, 1))
    return length, width, position_offset

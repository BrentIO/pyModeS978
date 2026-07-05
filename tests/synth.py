"""Synthetic UAT frame construction for tests.

Builds frames from the same absolute-bit-offset facts used throughout
src/pyModeS978 (verified against dump978/FlightAware's dump978 as field-layout
references only, per the project's GPL-reference-only policy -- nothing here
is copied from either). Not a decoder inverse-by-construction guarantee: this
is an independent encoder, and round-tripping it through pyModeS978.decode()
is itself part of what tests in this suite verify.
"""

from pyModeS978._enums import AltitudeSource

_BASE40_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ  .."


def pack(nbytes: int, fields: list[tuple[int, int, int]]) -> bytes:
    value = 0
    for start_bit, num_bits, field_value in fields:
        shift = nbytes * 8 - start_bit - num_bits
        value |= (field_value & ((1 << num_bits) - 1)) << shift
    return value.to_bytes(nbytes, "big")


def _encode_lat(lat: float) -> int:
    raw = lat if lat >= 0 else lat + 180
    return round(raw * 2**24 / 360)


def _encode_lon(lon: float) -> int:
    raw = lon if lon >= 0 else lon + 360
    return round(raw * 2**24 / 360)


def _encode_altitude(altitude: int | None) -> int:
    if altitude is None:
        return 0
    return round((altitude + 1000) / 25) + 1


def _encode_signed_velocity(value: int | None, *, supersonic: bool) -> int:
    if value is None:
        return 0
    magnitude = abs(value) // 4 if supersonic else abs(value)
    raw = (magnitude + 1) & 0x3FF
    if value < 0:
        raw |= 0x400
    return raw


def _base40_triplet(chars: str) -> int:
    indices = [_BASE40_ALPHABET.index(c) for c in chars]
    return indices[0] * 1600 + indices[1] * 40 + indices[2]


def build_frame(
    *,
    payload_type: int = 0,
    address_qualifier: int = 0,
    icao: int = 0x000000,
    length: int | None = None,
    # State Vector
    latitude: float | None = None,
    longitude: float | None = None,
    nic: int = 0,
    altitude: int | None = None,
    altitude_type: AltitudeSource = AltitudeSource.BARO,
    airground_state: int = 0,  # 0=airborne subsonic, 1=supersonic, 2=ground, 3=reserved
    ns_velocity: int | None = None,
    ew_velocity: int | None = None,
    groundspeed: int | None = None,
    track: float | None = None,
    track_type_code: int = 1,  # 1=track, 2=magnetic_heading, 3=true_heading
    vertical_rate: int | None = None,
    vr_source: AltitudeSource = AltitudeSource.GNSS,
    length_code: int = 0,
    width_code: int = 0,
    position_offset: bool = False,
    utc_coupled: bool = False,
    tisb_site_id: int = 0,
    # Mode Status
    category: int = 0,
    callsign: str | None = None,
    squawk: str | None = None,
    emergency_state: int = 0,
    version: int = 0,
    sil: int = 0,
    transmit_mso: int = 0,
    sda: int = 0,
    nac_p: int = 0,
    nac_v: int = 0,
    nic_baro: bool = False,
    uat_in: bool = False,
    es_in: bool = False,
    tcas_operational: bool = False,
    tcas_ra_active: bool = False,
    ident_active: bool = False,
    atc_services: bool = False,
    sil_supplement: int = 0,
    gva: int = 0,
    single_antenna: bool = False,
    nic_supplement_a: bool = False,
    # AUX SV
    altitude_secondary: int | None = None,
) -> bytes:
    """Build a full synthetic frame. Unset fields default to zero/unavailable."""
    if length is None:
        length = 18 if payload_type in (0, 4, 7, 8, 9, 10) else 34

    fields = [
        (0, 5, payload_type),
        (5, 3, address_qualifier),
        (8, 24, icao),
        (32, 23, _encode_lat(latitude) if latitude is not None else 0),
        (55, 24, _encode_lon(longitude) if longitude is not None else 0),
        (79, 1, 1 if altitude_type == AltitudeSource.GNSS else 0),
        (80, 12, _encode_altitude(altitude)),
        (92, 4, nic),
        (96, 2, airground_state),
    ]

    if airground_state in (0, 1):
        supersonic = airground_state == 1
        fields.append((99, 11, _encode_signed_velocity(ns_velocity, supersonic=supersonic)))
        fields.append((110, 11, _encode_signed_velocity(ew_velocity, supersonic=supersonic)))
        if vertical_rate is not None:
            raw_vvel = (abs(vertical_rate) // 64 + 1) & 0x1FF
            if vertical_rate < 0:
                raw_vvel |= 0x200
            if vr_source == AltitudeSource.BARO:
                raw_vvel |= 0x400
            fields.append((121, 11, raw_vvel))
    elif airground_state == 2:
        raw_gs = (groundspeed + 1) & 0x3FF if groundspeed is not None else 0
        fields.append((99, 11, raw_gs))
        if track is not None:
            raw_track = (track_type_code << 9) | round(track * 512 / 360)
            fields.append((110, 11, raw_track))
        fields.append((121, 4, width_code))
        fields.append((122, 3, length_code))
        fields.append((125, 1, 1 if position_offset else 0))

    if address_qualifier in (2, 3):
        fields.append((132, 4, tisb_site_id))
    else:
        fields.append((132, 1, 1 if utc_coupled else 0))

    if payload_type in (1, 3):
        callsign_text = (callsign or squawk or "").ljust(8)
        chars = [_BASE40_ALPHABET.index(" ")] * 8
        for i, ch in enumerate(callsign_text[:8]):
            chars[i] = _BASE40_ALPHABET.index(ch)
        word1 = category * 1600 + chars[0] * 40 + chars[1]
        word2 = chars[2] * 1600 + chars[3] * 40 + chars[4]
        word3 = chars[5] * 1600 + chars[6] * 40 + chars[7]

        fields.append((136, 16, word1))
        fields.append((152, 16, word2))
        fields.append((168, 16, word3))
        fields.append((184, 3, emergency_state))
        fields.append((187, 3, version))
        fields.append((190, 2, sil))
        fields.append((192, 6, transmit_mso))
        fields.append((198, 2, sda))
        fields.append((200, 4, nac_p))
        fields.append((204, 3, nac_v))
        fields.append((207, 1, 1 if nic_baro else 0))
        fields.append((208, 1, 1 if uat_in else 0))
        fields.append((209, 1, 1 if es_in else 0))
        fields.append((210, 1, 1 if tcas_operational else 0))
        fields.append((211, 1, 1 if tcas_ra_active else 0))
        fields.append((212, 1, 1 if ident_active else 0))
        fields.append((213, 1, 1 if atc_services else 0))
        fields.append((214, 1, 1 if callsign else 0))
        fields.append((215, 1, sil_supplement))
        fields.append((216, 2, gva))
        fields.append((218, 1, 1 if single_antenna else 0))
        fields.append((219, 1, 1 if nic_supplement_a else 0))

    if payload_type in (1, 2, 5, 6):
        fields.append((232, 12, _encode_altitude(altitude_secondary)))

    return pack(length, fields)

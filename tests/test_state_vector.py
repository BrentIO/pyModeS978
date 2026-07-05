import math

import pytest
from synth import pack as _pack

from pyModeS978._state_vector import decode

# Fixtures below (TEST1-3) were constructed independently of _state_vector.py's
# implementation, using the reference byte-mask formulas directly (see the
# scratch script used during development), not this module's absolute-bit-offset
# helper -- so matching them is a real cross-check, not circular verification.

# Airborne, subsonic: raw_lat=0x123456, raw_lon=0x654321, raw_alt=1000, nic=8,
# N/S=+100kt, E/W=-50kt, vertical_rate raw -> +640 ft/min (baro), utc_coupled=1.
_AIRBORNE_HEX = "000000002468ACCA86423E88019619C0B800"

# nic=0, raw_lat=0, raw_lon=0, airground_state=reserved (3).
_NO_POSITION_RESERVED_HEX = "000000000000000000000000C00000000000"

# Ground state: groundspeed raw->50kt, track type=track raw code 386 (271.40625 deg),
# width_code=7 -> length=85m, width=45m, position_offset=1.
_GROUND_HEX = "00000000000000000000000980CDC13C0500"


def test_airborne_position_altitude_velocity():
    result = decode(bytes.fromhex(_AIRBORNE_HEX), address_qualifier=0)
    assert result["latitude"] == pytest.approx(25.59999)
    assert result["longitude"] == pytest.approx(142.4)
    assert result["altitude"] == 23975
    assert result["altitude_type"] == "baro"
    assert result["nic"] == 8
    assert result["airground_state"] == "airborne"
    assert result["groundspeed"] == round(math.sqrt(100**2 + 50**2))
    assert result["track"] == 333.4
    assert result["heading"] is None
    assert result["heading_type"] is None
    assert result["vertical_rate"] == 640
    assert result["vr_source"] == "BARO"
    assert result["utc_coupled"] is True
    assert result["tisb_site_id"] is None
    assert result["length"] is None
    assert result["width"] is None
    assert result["position_offset"] is None


def test_tisb_site_id_instead_of_utc_coupled():
    # Same frame, but address_qualifier says TIS-B -> same nibble means site ID, not UTC-coupled.
    result = decode(bytes.fromhex(_AIRBORNE_HEX), address_qualifier=2)
    assert result["tisb_site_id"] == 0b1000
    assert result["utc_coupled"] is None


def test_no_position_and_reserved_airground_state():
    result = decode(bytes.fromhex(_NO_POSITION_RESERVED_HEX), address_qualifier=0)
    assert result["latitude"] is None
    assert result["longitude"] is None
    assert result["altitude"] is None
    assert result["altitude_type"] is None
    assert result["nic"] == 0
    assert result["airground_state"] == "reserved"
    assert result["groundspeed"] is None
    assert result["track"] is None
    assert result["heading"] is None
    assert result["heading_type"] is None
    assert result["vertical_rate"] is None
    assert result["vr_source"] is None


def test_position_valid_at_origin_when_nic_nonzero():
    # nic != 0 alone is enough to mark position "valid" even if raw lat/lon are both 0.
    result = decode(bytes.fromhex(_GROUND_HEX), address_qualifier=0)
    assert result["nic"] == 9
    assert result["latitude"] == 0.0
    assert result["longitude"] == 0.0


def test_ground_speed_track_and_dimensions():
    result = decode(bytes.fromhex(_GROUND_HEX), address_qualifier=0)
    assert result["airground_state"] == "ground"
    assert result["groundspeed"] == 50
    assert result["track"] == 271.4
    assert result["heading"] is None
    assert result["heading_type"] is None
    assert result["length"] == 85
    assert result["width"] == 45
    assert result["position_offset"] is True
    # Vertical rate is not defined on the ground -- those bits are dimensions instead.
    assert result["vertical_rate"] is None
    assert result["vr_source"] is None


def test_supersonic_velocity_multiplier():
    # airground_state=1 (supersonic); N/S and E/W raw magnitude 11 (-> 10 before x4), both positive.
    raw = (0 << 10) | 11
    payload = _pack(
        18,
        [
            (96, 2, 1),  # airground_state = supersonic
            (99, 11, raw),  # N/S
            (110, 11, raw),  # E/W
        ],
    )
    result = decode(payload, address_qualifier=0)
    assert result["airground_state"] == "airborne"
    # magnitude 11 -> 10 kt, x4 for supersonic -> 40 kt on each axis
    assert result["groundspeed"] == round(math.sqrt(40**2 + 40**2))
    assert result["track"] == 45.0  # equal N/S and E/W -> 45 degrees


def test_ground_invalid_type_code():
    payload = _pack(
        18,
        [
            (96, 2, 2),  # airground_state = ground
            (99, 11, 51),  # groundspeed raw -> 50kt
            (110, 11, 0b00_100000000),  # type code 0 (invalid), magnitude bits irrelevant
        ],
    )
    result = decode(payload, address_qualifier=0)
    assert result["groundspeed"] == 50
    assert result["track"] is None
    assert result["heading"] is None
    assert result["heading_type"] is None


def test_ground_magnetic_heading():
    # type code 2 (magnetic heading), value code 386 -> 271.40625 deg
    raw_track = (2 << 9) | 386
    payload = _pack(18, [(96, 2, 2), (110, 11, raw_track)])
    result = decode(payload, address_qualifier=0)
    assert result["track"] is None
    assert result["heading"] == 271.4
    assert result["heading_type"] == "magnetic"


def test_ground_true_heading():
    # type code 3 (true heading), value code 386 -> 271.40625 deg
    raw_track = (3 << 9) | 386
    payload = _pack(18, [(96, 2, 2), (110, 11, raw_track)])
    result = decode(payload, address_qualifier=0)
    assert result["track"] is None
    assert result["heading"] == 271.4
    assert result["heading_type"] == "true"

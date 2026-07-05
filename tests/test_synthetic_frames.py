import math

import pytest
from synth import build_frame

import pyModeS978
from pyModeS978._enums import AirgroundState, AltitudeSource, EmitterCategory, HeadingType


def test_position_unavailable_when_nic_zero():
    frame = build_frame(payload_type=0, nic=0)
    result = pyModeS978.decode(frame.hex())
    assert result["latitude"] is None
    assert result["longitude"] is None


def test_position_valid_at_origin_when_nic_nonzero():
    frame = build_frame(payload_type=0, nic=5)
    result = pyModeS978.decode(frame.hex())
    assert result["latitude"] == 0.0
    assert result["longitude"] == 0.0


def test_position_realistic_coordinates():
    frame = build_frame(payload_type=0, nic=9, latitude=28.5, longitude=-81.6)
    result = pyModeS978.decode(frame.hex())
    assert result["latitude"] == pytest.approx(28.5, abs=1e-4)
    assert result["longitude"] == pytest.approx(-81.6, abs=1e-4)


def test_altitude_unavailable():
    frame = build_frame(payload_type=0, altitude=None)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude"] is None
    assert result["altitude_type"] is None


def test_altitude_available():
    frame = build_frame(payload_type=0, altitude=35000, altitude_type=AltitudeSource.GNSS)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude"] == 35000
    assert result["altitude_type"] == AltitudeSource.GNSS


def test_airborne_velocity_and_vertical_rate():
    frame = build_frame(
        payload_type=0,
        airground_state=0,
        ns_velocity=100,
        ew_velocity=-50,
        vertical_rate=-640,
        vr_source=AltitudeSource.BARO,
    )
    result = pyModeS978.decode(frame.hex())
    assert result["airground_state"] == AirgroundState.AIRBORNE_SUBSONIC
    assert result["groundspeed"] == round(math.sqrt(100**2 + 50**2))
    assert result["track"] == round((360 + 90 - math.degrees(math.atan2(100, -50))) % 360, 1)
    assert result["heading"] is None
    assert result["heading_type"] is None
    assert result["vertical_rate"] == -640
    assert result["vr_source"] == AltitudeSource.BARO


def test_supersonic_velocity_multiplier():
    frame = build_frame(payload_type=0, airground_state=1, ns_velocity=40, ew_velocity=40)
    result = pyModeS978.decode(frame.hex())
    assert result["groundspeed"] == round(math.sqrt(40**2 + 40**2))
    assert result["track"] == 45.0


def test_ground_velocity_and_track():
    frame = build_frame(
        payload_type=0,
        airground_state=2,
        groundspeed=50,
        track=271.40625,
        track_type_code=1,
    )
    result = pyModeS978.decode(frame.hex())
    assert result["airground_state"] == AirgroundState.ON_GROUND
    assert result["groundspeed"] == 50
    assert result["track"] == 271.4
    assert result["heading"] is None
    assert result["heading_type"] is None
    assert result["vertical_rate"] is None


def test_ground_magnetic_heading():
    frame = build_frame(
        payload_type=0,
        airground_state=2,
        track=271.40625,
        track_type_code=2,
    )
    result = pyModeS978.decode(frame.hex())
    assert result["track"] is None
    assert result["heading"] == 271.4
    assert result["heading_type"] == HeadingType.MAGNETIC


def test_ground_dimensions():
    frame = build_frame(
        payload_type=0,
        airground_state=2,
        length_code=7,
        width_code=7,
        position_offset=True,
    )
    result = pyModeS978.decode(frame.hex())
    assert result["length"] == 85
    assert result["width"] == 45
    assert result["position_offset"] is True


def test_reserved_airground_state_has_no_velocity_or_dimensions():
    frame = build_frame(payload_type=0, airground_state=3)
    result = pyModeS978.decode(frame.hex())
    assert result["airground_state"] == AirgroundState.RESERVED
    assert result["groundspeed"] is None
    assert result["track"] is None
    assert result["vertical_rate"] is None
    assert result["length"] is None
    assert result["width"] is None


def test_tisb_address_qualifier_yields_site_id_not_utc_coupled():
    frame = build_frame(payload_type=0, address_qualifier=2, tisb_site_id=5)
    result = pyModeS978.decode(frame.hex())
    assert result["tisb_site_id"] == 5
    assert result["utc_coupled"] is None


def test_native_adsb_yields_utc_coupled_not_site_id():
    frame = build_frame(payload_type=0, address_qualifier=0, utc_coupled=True)
    result = pyModeS978.decode(frame.hex())
    assert result["utc_coupled"] is True
    assert result["tisb_site_id"] is None


def test_callsign_case():
    frame = build_frame(payload_type=1, callsign="N12345", category=1)
    result = pyModeS978.decode(frame.hex())
    assert result["callsign"] == "N12345"
    assert result["squawk"] is None
    assert result["category"] is EmitterCategory.LIGHT


def test_squawk_case():
    frame = build_frame(payload_type=1, squawk="1200")
    result = pyModeS978.decode(frame.hex())
    assert result["squawk"] == "1200"
    assert result["callsign"] is None


def test_blank_mode_status_field():
    frame = build_frame(payload_type=1)
    result = pyModeS978.decode(frame.hex())
    assert result["callsign"] is None
    assert result["squawk"] is None


def test_aux_sv_present_with_opposite_type():
    frame = build_frame(payload_type=1, altitude_type=AltitudeSource.BARO, altitude_secondary=5000)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude_secondary"] == 5000
    assert result["altitude_secondary_type"] == AltitudeSource.GNSS


def test_aux_sv_absent_for_sv_only_type():
    frame = build_frame(payload_type=0, altitude_secondary=5000)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude_secondary"] is None
    assert result["altitude_secondary_type"] is None


def test_nic_containment_radius_resolvable():
    frame = build_frame(payload_type=1, nic=11, nic_supplement_a=False)
    result = pyModeS978.decode(frame.hex())
    assert result["position_containment_radius_m"] == 7.5
    assert result["position_vpl_m"] == 11


def test_nic_containment_radius_unresolvable_combination():
    frame = build_frame(payload_type=1, nic=9, nic_supplement_a=False)
    result = pyModeS978.decode(frame.hex())
    assert result["position_containment_radius_m"] is None


@pytest.mark.parametrize(
    "payload_type,has_sv,has_ms,has_auxsv",
    [
        (0, True, False, False),
        (4, True, False, False),
        (7, True, False, False),
        (8, True, False, False),
        (9, True, False, False),
        (10, True, False, False),
        (1, True, True, True),
        (2, True, False, True),
        (5, True, False, True),
        (6, True, False, True),
        (3, True, True, False),
        (11, False, False, False),
        (20, False, False, False),
        (31, False, False, False),
    ],
)
def test_payload_type_dispatch(payload_type, has_sv, has_ms, has_auxsv):
    frame = build_frame(
        payload_type=payload_type,
        nic=5,
        callsign="N12345",
        category=1,
        altitude_secondary=5000,
    )
    result = pyModeS978.decode(frame.hex())
    assert (result["nic"] is not None) is has_sv
    assert (result["callsign"] is not None) is has_ms
    assert (result["altitude_secondary"] is not None) is has_auxsv


def test_uplink_returns_none():
    assert pyModeS978.decode("+" + "00" * 432) is None


def test_malformed_input_returns_none():
    assert pyModeS978.decode("not valid hex") is None

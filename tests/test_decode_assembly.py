from synth import build_frame
from synth import pack as _pack

import pyModeS978
from pyModeS978._enums import AltitudeSource


def _frame_with_payload_type(payload_type: int) -> bytes:
    # nic=5 (SV marker), category=1/callsign="55000000" (MS marker, callsign_type
    # bit set), altitude_secondary raw=1000 (AUX SV marker) -- present regardless of
    # payload_type, so a leaked/missing block shows up as an unexpected value vs None.
    group1 = 1 * 1600 + 5 * 40 + 5
    return _pack(
        34,
        [
            (0, 5, payload_type),
            (5, 3, 0),  # address_qualifier
            (8, 24, 0xABCDEF),  # icao
            (92, 4, 5),  # nic
            (136, 16, group1),
            (214, 1, 1),  # callsign_type = callsign
            (232, 12, 1000),  # AUX SV raw altitude
        ],
    )


def test_sv_only_type():
    result = pyModeS978.decode(_frame_with_payload_type(0).hex())
    assert result["icao"] == "ABCDEF"
    assert result["nic"] == 5
    assert result["category"] is None
    assert result["callsign"] is None
    assert result["altitude_secondary"] is None


def test_sv_ms_auxsv_type():
    result = pyModeS978.decode(_frame_with_payload_type(1).hex())
    assert result["nic"] == 5
    assert result["category"] is not None
    assert result["callsign"] == "55000000"
    assert result["altitude_secondary"] == 23975


def test_sv_auxsv_type():
    result = pyModeS978.decode(_frame_with_payload_type(2).hex())
    assert result["nic"] == 5
    assert result["category"] is None
    assert result["callsign"] is None
    assert result["altitude_secondary"] == 23975


def test_sv_ms_type():
    result = pyModeS978.decode(_frame_with_payload_type(3).hex())
    assert result["nic"] == 5
    assert result["category"] is not None
    assert result["callsign"] == "55000000"
    assert result["altitude_secondary"] is None


def test_reserved_sv_only_types():
    for payload_type in (4, 7, 8, 9, 10):
        result = pyModeS978.decode(_frame_with_payload_type(payload_type).hex())
        assert result["nic"] == 5, payload_type
        assert result["category"] is None, payload_type
        assert result["altitude_secondary"] is None, payload_type


def test_sv_auxsv_variant_types():
    for payload_type in (5, 6):
        result = pyModeS978.decode(_frame_with_payload_type(payload_type).hex())
        assert result["nic"] == 5, payload_type
        assert result["altitude_secondary"] == 23975, payload_type
        assert result["category"] is None, payload_type


def test_hdr_only_type():
    result = pyModeS978.decode(_frame_with_payload_type(15).hex())
    assert result["icao"] == "ABCDEF"
    assert result["nic"] is None
    assert result["category"] is None
    assert result["callsign"] is None
    assert result["altitude_secondary"] is None


def test_uplink_returns_none():
    assert pyModeS978.decode("+" + "00" * 432) is None


def test_geo_minus_baro_baro_primary():
    frame = build_frame(
        payload_type=1, altitude=1000, altitude_type=AltitudeSource.BARO, altitude_secondary=1200
    )
    result = pyModeS978.decode(frame.hex())
    assert result["altitude"] == 1000
    assert result["altitude_secondary"] == 1200
    assert result["geo_minus_baro"] == 200


def test_geo_minus_baro_gnss_primary():
    frame = build_frame(
        payload_type=1, altitude=1200, altitude_type=AltitudeSource.GNSS, altitude_secondary=1000
    )
    result = pyModeS978.decode(frame.hex())
    assert result["altitude"] == 1200
    assert result["altitude_secondary"] == 1000
    assert result["geo_minus_baro"] == 200


def test_geo_minus_baro_none_without_auxsv():
    # payload_type=0 -- no AUX SV block, so altitude_secondary is always None.
    frame = build_frame(payload_type=0, altitude=1000, altitude_type=AltitudeSource.BARO)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude_secondary"] is None
    assert result["geo_minus_baro"] is None


def test_geo_minus_baro_none_when_primary_altitude_unavailable():
    frame = build_frame(payload_type=1, altitude=None, altitude_secondary=1200)
    result = pyModeS978.decode(frame.hex())
    assert result["altitude"] is None
    assert result["altitude_secondary"] == 1200
    assert result["geo_minus_baro"] is None

import pyModeS978
from pyModeS978 import _aux_sv, _mode_status, _state_vector


def test_decode_invalid_input_returns_none():
    assert pyModeS978.decode("not valid hex") is None


def test_decode_returns_all_fields():
    result = pyModeS978.decode("00" * 18)
    assert result is not None

    expected_keys = (
        {"direction", "payload_type", "address_qualifier", "icao"}
        | set(_state_vector.FIELDS)
        | set(_mode_status.FIELDS)
        | set(_aux_sv.FIELDS)
    )
    assert set(result.keys()) == expected_keys
    assert result["icao"] == "000000"

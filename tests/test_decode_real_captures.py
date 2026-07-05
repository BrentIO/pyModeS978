import json
from pathlib import Path

import pytest

import pyModeS978
from pyModeS978 import _aux_sv, _mode_status, _state_vector, _uncertainty

_FIXTURE = Path(__file__).parent / "fixtures" / "uat-example.ndjson"
_RECORDS = [json.loads(line) for line in _FIXTURE.read_text().splitlines() if line.strip()]

_EXPECTED_KEYS = (
    {"direction", "payload_type", "address_qualifier", "icao"}
    | set(_state_vector.FIELDS)
    | set(_mode_status.FIELDS)
    | set(_aux_sv.FIELDS)
    | set(_uncertainty.FIELDS)
)


@pytest.mark.parametrize("record", _RECORDS, ids=[r["icao_hex"] for r in _RECORDS])
def test_real_capture_decodes_without_crashing(record):
    result = pyModeS978.decode(record["raw"])
    assert result is not None
    assert set(result.keys()) == _EXPECTED_KEYS
    assert result["icao"] == record["icao_hex"]
    assert result["direction"] == "downlink"

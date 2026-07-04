import json
from pathlib import Path

import pytest

from pyModeS978._frame import parse
from pyModeS978._state_vector import decode

_FIXTURE = Path(__file__).parent / "fixtures" / "uat-example.ndjson"
_RECORDS = [json.loads(line) for line in _FIXTURE.read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("record", _RECORDS, ids=[r["icao_hex"] for r in _RECORDS])
def test_real_capture_state_vector_decodes_without_crashing(record):
    frame = parse(record["raw"])
    assert frame is not None

    result = decode(frame.payload, frame.address_qualifier)

    if result["latitude"] is not None:
        assert -90 <= result["latitude"] <= 90
    if result["longitude"] is not None:
        assert -180 <= result["longitude"] <= 180
    if result["altitude"] is not None:
        assert -1000 <= result["altitude"] <= 100_000
    if result["groundspeed"] is not None:
        assert 0 <= result["groundspeed"] < 4000
    if result["track"] is not None:
        assert 0 <= result["track"] < 360
    assert result["airground_state"] in {"airborne", "ground", "reserved"}

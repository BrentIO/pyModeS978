import json
from pathlib import Path

import pytest

from pyModeS978._enums import PayloadType
from pyModeS978._frame import parse
from pyModeS978._mode_status import decode

_FIXTURE = Path(__file__).parent / "fixtures" / "uat-example.ndjson"
_RECORDS = [json.loads(line) for line in _FIXTURE.read_text().splitlines() if line.strip()]
_MS_RECORDS = [
    r for r in _RECORDS if parse(r["raw"]) and parse(r["raw"]).payload_type in (
        PayloadType.LONG, PayloadType.SHORT_MS
    )
]


def test_fixture_has_mode_status_bearing_records():
    # Sanity check that this fixture actually exercises the code path at all.
    assert len(_MS_RECORDS) > 0


@pytest.mark.parametrize("record", _MS_RECORDS, ids=[r["icao_hex"] for r in _MS_RECORDS])
def test_real_capture_mode_status_decodes_without_crashing(record):
    frame = parse(record["raw"])
    assert frame is not None

    result = decode(frame.payload)

    assert not (result["callsign"] and result["squawk"])  # mutually exclusive
    if result["callsign"] is not None:
        assert 1 <= len(result["callsign"]) <= 8
    if result["squawk"] is not None:
        assert 1 <= len(result["squawk"]) <= 8
    assert 0 <= result["mops_version"] <= 7
    assert 0 <= result["sil"] <= 3
    assert 0 <= result["sda"] <= 3
    assert 0 <= result["nac_p"] <= 15
    assert 0 <= result["nac_v"] <= 7
    assert 0 <= result["gva"] <= 3

import json
from pathlib import Path

import pytest

from pyModeS978._frame import parse

_FIXTURE = Path(__file__).parent / "fixtures" / "uat-example.ndjson"
_RECORDS = [json.loads(line) for line in _FIXTURE.read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("record", _RECORDS, ids=[r["icao_hex"] for r in _RECORDS])
def test_real_capture_parses_and_matches_icao(record):
    result = parse(record["raw"])
    assert result is not None
    assert result.icao == record["icao_hex"]

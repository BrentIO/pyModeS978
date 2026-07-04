import re
from dataclasses import dataclass

from ._bits import read_uint

_DOWNLINK_LENGTHS = {18, 34}
_UPLINK_LENGTH = 432

_HEX_RE = re.compile(r"^[0-9A-Fa-f]+$")


@dataclass(frozen=True)
class ParsedFrame:
    direction: str
    payload: bytes
    payload_type: int
    address_qualifier: int
    icao: str


def parse(raw: str) -> ParsedFrame | None:
    raw = raw.split(";", 1)[0]

    asserted_direction = None
    if raw.startswith("-"):
        asserted_direction = "downlink"
        raw = raw[1:]
    elif raw.startswith("+"):
        asserted_direction = "uplink"
        raw = raw[1:]

    if not raw or len(raw) % 2 != 0 or not _HEX_RE.match(raw):
        return None

    payload = bytes.fromhex(raw)
    length = len(payload)

    if length in _DOWNLINK_LENGTHS:
        direction = "downlink"
    elif length == _UPLINK_LENGTH:
        direction = "uplink"
    else:
        return None

    if asserted_direction is not None and asserted_direction != direction:
        return None

    if direction == "uplink":
        return None

    payload_type = read_uint(payload, 0, 5)
    address_qualifier = read_uint(payload, 5, 3)
    icao = f"{read_uint(payload, 8, 24):06X}"

    return ParsedFrame(
        direction=direction,
        payload=payload,
        payload_type=payload_type,
        address_qualifier=address_qualifier,
        icao=icao,
    )

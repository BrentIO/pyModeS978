from pyModeS978._frame import ParsedFrame, parse

# payload_type=1 (00001), address_qualifier=0 (000) -> byte0 = 0000_1000 = 0x08
# icao = 0xABCDEF (bytes 1-3)
_HDR_HEX = "08ABCDEF"
_SHORT_DOWNLINK = _HDR_HEX + "00" * 14  # 18 bytes total
_LONG_DOWNLINK = _HDR_HEX + "00" * 30  # 34 bytes total
_UPLINK = "00" * 432


def test_short_downlink_no_prefix():
    result = parse(_SHORT_DOWNLINK)
    assert result == ParsedFrame(
        direction="downlink",
        payload=bytes.fromhex(_SHORT_DOWNLINK),
        payload_type=1,
        address_qualifier=0,
        icao="ABCDEF",
    )


def test_short_downlink_with_prefix():
    result = parse("-" + _SHORT_DOWNLINK)
    assert result is not None
    assert result.direction == "downlink"
    assert result.icao == "ABCDEF"


def test_long_downlink_with_prefix():
    result = parse("-" + _LONG_DOWNLINK)
    assert result is not None
    assert result.direction == "downlink"
    assert len(result.payload) == 34


def test_metadata_suffix_is_stripped():
    result = parse("-" + _SHORT_DOWNLINK + ";t=123.456;rs=0")
    assert result is not None
    assert result.icao == "ABCDEF"


def test_lowercase_hex_accepted():
    result = parse("-" + _SHORT_DOWNLINK.lower())
    assert result is not None
    assert result.icao == "ABCDEF"


def test_uplink_returns_none():
    assert parse(_UPLINK) is None


def test_uplink_with_prefix_returns_none():
    assert parse("+" + _UPLINK) is None


def test_mismatched_prefix_and_length_returns_none():
    # "-" (downlink) prefix on a 432-byte uplink-length payload is contradictory
    assert parse("-" + _UPLINK) is None
    # "+" (uplink) prefix on a valid downlink-length payload is contradictory
    assert parse("+" + _SHORT_DOWNLINK) is None


def test_invalid_length_returns_none():
    assert parse("00" * 20) is None  # not 18, 34, or 432 bytes


def test_non_hex_characters_returns_none():
    assert parse("ZZ" + _SHORT_DOWNLINK[2:]) is None


def test_odd_length_hex_returns_none():
    assert parse(_SHORT_DOWNLINK[:-1]) is None


def test_empty_string_returns_none():
    assert parse("") is None
    assert parse("-") is None

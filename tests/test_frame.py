import pytest

from pyModeS978._enums import AddressQualifier, PayloadType
from pyModeS978._errors import DirectionMismatchError, InvalidHexError, InvalidLengthError
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


def test_payload_type_and_address_qualifier_are_named_enums():
    result = parse(_SHORT_DOWNLINK)
    assert result.payload_type is PayloadType.LONG
    assert result.address_qualifier is AddressQualifier.ADSB_ICAO


def test_unrecognized_payload_type_falls_back_to_plain_int():
    # payload_type=4 (00100), address_qualifier=0 (000) -> byte0 = 0010_0000 = 0x20
    hdr = "20ABCDEF" + "00" * 14
    result = parse(hdr)
    assert result.payload_type == 4
    assert not isinstance(result.payload_type, PayloadType)


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


def test_mismatched_prefix_and_length_raises():
    # "-" (downlink) prefix on a 432-byte uplink-length payload is contradictory
    with pytest.raises(DirectionMismatchError) as exc_info:
        parse("-" + _UPLINK)
    assert exc_info.value.asserted == "downlink"
    assert exc_info.value.actual == "uplink"
    assert exc_info.value.raw == "-" + _UPLINK

    # "+" (uplink) prefix on a valid downlink-length payload is contradictory
    with pytest.raises(DirectionMismatchError) as exc_info:
        parse("+" + _SHORT_DOWNLINK)
    assert exc_info.value.asserted == "uplink"
    assert exc_info.value.actual == "downlink"
    assert exc_info.value.raw == "+" + _SHORT_DOWNLINK


def test_invalid_length_raises():
    with pytest.raises(InvalidLengthError) as exc_info:
        parse("00" * 20)  # not 18, 34, or 432 bytes
    assert exc_info.value.actual == 20
    assert exc_info.value.expected == (18, 34, 432)
    assert exc_info.value.raw == "00" * 20


def test_non_hex_characters_raises():
    with pytest.raises(InvalidHexError) as exc_info:
        parse("ZZ" + _SHORT_DOWNLINK[2:])
    assert exc_info.value.raw == "ZZ" + _SHORT_DOWNLINK[2:]


def test_invalid_hex_error_raw_is_the_original_unstripped_input():
    # .raw should be the full original input (prefix and metadata intact),
    # not the intermediate string left after stripping either of them.
    bad = "-ZZ" + _SHORT_DOWNLINK[2:] + ";t=123.456"
    with pytest.raises(InvalidHexError) as exc_info:
        parse(bad)
    assert exc_info.value.raw == bad


def test_odd_length_hex_raises():
    with pytest.raises(InvalidHexError):
        parse(_SHORT_DOWNLINK[:-1])


def test_empty_string_raises():
    with pytest.raises(InvalidHexError):
        parse("")
    with pytest.raises(InvalidHexError):
        parse("-")

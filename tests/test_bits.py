from pyModeS978._bits import read_uint


def test_read_uint_full_byte():
    assert read_uint(b"\xff", 0, 8) == 0xFF


def test_read_uint_top_nibble():
    assert read_uint(b"\xf0", 0, 4) == 0xF


def test_read_uint_bottom_nibble():
    assert read_uint(b"\x0f", 4, 4) == 0xF


def test_read_uint_spans_bytes():
    # 0x01 0x23 -> bits 4..15 (12 bits) = 0x123
    assert read_uint(b"\x01\x23", 4, 12) == 0x123


def test_read_uint_hdr_split():
    # byte0 = 0000 1000 -> top 5 bits = 00001 (1), next 3 bits = 000 (0)
    payload = b"\x08"
    assert read_uint(payload, 0, 5) == 1
    assert read_uint(payload, 5, 3) == 0

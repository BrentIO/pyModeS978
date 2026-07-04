from pyModeS978._enums import Emergency, EmitterCategory
from pyModeS978._mode_status import decode

# Fixtures below were constructed independently of _mode_status.py's implementation,
# using the reference's own byte-mask/base-40 formulas (see the scratch script used
# during development), not this module's read_uint-based implementation -- so
# matching them is a real cross-check, not circular verification.

# Callsign "N12345", emitter=LIGHT, emergency=MEDICAL, uat_version=2, sil=3,
# transmit_mso=42, nac_p=9, nac_v=3, nic_baro=1, has_cdti=1, ident_active=1,
# heading_type=magnetic, callsign_type=callsign.
_CALLSIGN_HEX = "080000000000000000000000000000000009D90CFC25044BA8979600000000000000"

# Squawk "1200", has_acas=1, acas_ra_active=1, atc_services=1, heading_type=true,
# sil=2, callsign_type=squawk.
_SQUAWK_HEX = "0800000000000000000000000000000000002A0024E6C40A00006800000000000000"

# Blank callsign/squawk field (all spaces), emitter=HEAVY, emergency=reserved(7).
_BLANK_HEX = "08000000000000000000000000000000002504E6C4E6C4E000000200000000000000"


def test_callsign_decode():
    result = decode(bytes.fromhex(_CALLSIGN_HEX))
    assert result["callsign"] == "N12345"
    assert result["squawk"] is None
    assert result["emitter_category"] is EmitterCategory.LIGHT
    assert result["emergency"] is Emergency.MEDICAL
    assert result["uat_version"] == 2
    assert result["sil"] == 3
    assert result["transmit_mso"] == 42
    assert result["nac_p"] == 9
    assert result["nac_v"] == 3
    assert result["nic_baro"] is True
    assert result["has_cdti"] is True
    assert result["has_acas"] is False
    assert result["acas_ra_active"] is False
    assert result["ident_active"] is True
    assert result["atc_services"] is False
    assert result["heading_type"] == "magnetic"


def test_squawk_decode():
    result = decode(bytes.fromhex(_SQUAWK_HEX))
    assert result["squawk"] == "1200"
    assert result["callsign"] is None
    assert result["has_acas"] is True
    assert result["acas_ra_active"] is True
    assert result["atc_services"] is True
    assert result["heading_type"] == "true"
    assert result["sil"] == 2


def test_blank_field_yields_neither_callsign_nor_squawk():
    result = decode(bytes.fromhex(_BLANK_HEX))
    assert result["callsign"] is None
    assert result["squawk"] is None
    assert result["emitter_category"] is EmitterCategory.HEAVY
    assert result["emergency"] is Emergency.RESERVED_7


def _pack(nbytes: int, fields: list[tuple[int, int, int]]) -> bytes:
    value = 0
    for start_bit, num_bits, field_value in fields:
        shift = nbytes * 8 - start_bit - num_bits
        value |= (field_value & ((1 << num_bits) - 1)) << shift
    return value.to_bytes(nbytes, "big")


def test_reserved_emergency_code_still_decodes():
    # emergency_status is a 3-bit field (0-7) and all 8 values are named (including the
    # spec's reserved slot), so every possible raw value resolves to a real member --
    # unlike PayloadType/AddressQualifier, there's no gap here to exercise coerce()'s
    # int-fallback path.
    payload = _pack(34, [(184, 3, 7)])
    result = decode(payload)
    assert result["emergency"] is Emergency.RESERVED_7

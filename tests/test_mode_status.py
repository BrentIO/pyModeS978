from synth import pack as _pack

from pyModeS978._enums import Emergency, EmitterCategory, SILSupplement
from pyModeS978._mode_status import decode

# Fixtures below were constructed independently of _mode_status.py's implementation,
# using the reference's own byte-mask/base-40 formulas (see the scratch script used
# during development), not this module's read_uint-based implementation -- so
# matching them is a real cross-check, not circular verification.

# Callsign "N12345", full set of Mode Status flags exercised (capability codes,
# operational modes, sil_supplement, gva, single_antenna, nic_supplement_a).
_CALLSIGN_HEX = "080000000000000000000000000000000009D90CFC25044BA997ABB0000000000000"

# Squawk "1200", opposite set of flags from TEST1.
_SQUAWK_HEX = "0800000000000000000000000000000000002A0024E6C40600005400000000000000"

# Blank callsign/squawk field (all spaces), emitter=HEAVY, emergency=reserved(7).
_BLANK_HEX = "08000000000000000000000000000000002504E6C4E6C4E000000200000000000000"


def test_callsign_decode():
    result = decode(bytes.fromhex(_CALLSIGN_HEX))
    assert result["callsign"] == "N12345"
    assert result["squawk"] is None
    assert result["category"] is EmitterCategory.LIGHT
    assert result["emergency"] is Emergency.MEDICAL
    assert result["version"] == 2
    assert result["sil"] == 3
    assert result["transmit_mso"] == 42
    assert result["sda"] == 1
    assert result["nac_p"] == 9
    assert result["nac_v"] == 3
    assert result["nic_baro"] is True
    assert result["uat_in"] is True
    assert result["es_in"] is False
    assert result["tcas_operational"] is True
    assert result["tcas_ra_active"] is False
    assert result["ident_active"] is True
    assert result["atc_services"] is False
    assert result["sil_supplement"] is SILSupplement.PER_SAMPLE
    assert result["gva"] == 2
    assert result["single_antenna"] is True
    assert result["nic_supplement_a"] is True


def test_squawk_decode():
    result = decode(bytes.fromhex(_SQUAWK_HEX))
    assert result["squawk"] == "1200"
    assert result["callsign"] is None
    assert result["version"] == 1
    assert result["sil"] == 2
    assert result["sda"] == 0
    assert result["uat_in"] is False
    assert result["es_in"] is True
    assert result["tcas_operational"] is False
    assert result["tcas_ra_active"] is True
    assert result["ident_active"] is False
    assert result["atc_services"] is True
    assert result["sil_supplement"] is SILSupplement.PER_HOUR
    assert result["gva"] == 0
    assert result["single_antenna"] is False
    assert result["nic_supplement_a"] is False


def test_blank_field_yields_neither_callsign_nor_squawk():
    result = decode(bytes.fromhex(_BLANK_HEX))
    assert result["callsign"] is None
    assert result["squawk"] is None
    assert result["category"] is EmitterCategory.HEAVY
    assert result["emergency"] is Emergency.RESERVED_7


def test_reserved_emergency_code_still_decodes():
    # emergency_status is a 3-bit field (0-7) and all 8 values are named (including the
    # spec's reserved slot), so every possible raw value resolves to a real member --
    # unlike PayloadType/AddressQualifier, there's no gap here to exercise coerce()'s
    # int-fallback path.
    payload = _pack(34, [(184, 3, 7)])
    result = decode(payload)
    assert result["emergency"] is Emergency.RESERVED_7

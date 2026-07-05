from ._bits import read_uint
from ._enums import Emergency, EmitterCategory, SILSupplement, coerce

_BASE40_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ  .."

FIELDS = (
    "category",
    "callsign",
    "squawk",
    "emergency_state",
    "version",
    "sil",
    "transmit_mso",
    "sda",
    "nac_p",
    "nac_v",
    "nic_baro",
    "uat_in",
    "es_in",
    "tcas_operational",
    "tcas_ra_active",
    "ident_active",
    "atc_services",
    "sil_supplement",
    "gva",
    "single_antenna",
    "nic_supplement_a",
)


def _base40_chars(raw16: int) -> str:
    return (
        _BASE40_ALPHABET[(raw16 // 1600) % 40]
        + _BASE40_ALPHABET[(raw16 // 40) % 40]
        + _BASE40_ALPHABET[raw16 % 40]
    )


def decode(payload: bytes) -> dict:
    group1 = read_uint(payload, 136, 16)
    group2 = read_uint(payload, 152, 16)
    group3 = read_uint(payload, 168, 16)

    category = coerce(EmitterCategory, (group1 // 1600) % 40)
    chars = _base40_chars(group1)[1:] + _base40_chars(group2) + _base40_chars(group3)

    callsign = squawk = None
    if chars[0] != " ":
        text = chars.rstrip(" ")
        if read_uint(payload, 214, 1):
            callsign = text
        else:
            squawk = text

    emergency = coerce(Emergency, read_uint(payload, 184, 3))
    version = read_uint(payload, 187, 3)
    sil = read_uint(payload, 190, 2)
    transmit_mso = read_uint(payload, 192, 6)
    sda = read_uint(payload, 198, 2)
    nac_p = read_uint(payload, 200, 4)
    nac_v = read_uint(payload, 204, 3)
    nic_baro = bool(read_uint(payload, 207, 1))

    # §2.2.4.5.4.12 "CAPABILITY CODES"
    uat_in = bool(read_uint(payload, 208, 1))
    es_in = bool(read_uint(payload, 209, 1))
    tcas_operational = bool(read_uint(payload, 210, 1))

    # §2.2.4.5.4.13 "OPERATIONAL MODES"
    tcas_ra_active = bool(read_uint(payload, 211, 1))
    ident_active = bool(read_uint(payload, 212, 1))
    atc_services = bool(read_uint(payload, 213, 1))

    sil_supplement = coerce(SILSupplement, read_uint(payload, 215, 1))
    gva = read_uint(payload, 216, 2)
    single_antenna = bool(read_uint(payload, 218, 1))
    nic_supplement_a = bool(read_uint(payload, 219, 1))

    return {
        "category": category,
        "callsign": callsign,
        "squawk": squawk,
        "emergency_state": emergency,
        "version": version,
        "sil": sil,
        "transmit_mso": transmit_mso,
        "sda": sda,
        "nac_p": nac_p,
        "nac_v": nac_v,
        "nic_baro": nic_baro,
        "uat_in": uat_in,
        "es_in": es_in,
        "tcas_operational": tcas_operational,
        "tcas_ra_active": tcas_ra_active,
        "ident_active": ident_active,
        "atc_services": atc_services,
        "sil_supplement": sil_supplement,
        "gva": gva,
        "single_antenna": single_antenna,
        "nic_supplement_a": nic_supplement_a,
    }

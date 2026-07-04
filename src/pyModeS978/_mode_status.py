from ._bits import read_uint
from ._enums import Emergency, EmitterCategory, coerce

_BASE40_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ  .."


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

    emitter_category = coerce(EmitterCategory, (group1 // 1600) % 40)
    chars = _base40_chars(group1)[1:] + _base40_chars(group2) + _base40_chars(group3)

    callsign = squawk = None
    if chars[0] != " ":
        text = chars.rstrip(" ")
        if read_uint(payload, 214, 1):
            callsign = text
        else:
            squawk = text

    emergency = coerce(Emergency, read_uint(payload, 184, 3))
    uat_version = read_uint(payload, 187, 3)
    sil = read_uint(payload, 190, 2)
    transmit_mso = read_uint(payload, 192, 6)
    nac_p = read_uint(payload, 200, 4)
    nac_v = read_uint(payload, 204, 3)
    nic_baro = bool(read_uint(payload, 207, 1))
    has_cdti = bool(read_uint(payload, 208, 1))
    has_acas = bool(read_uint(payload, 209, 1))
    acas_ra_active = bool(read_uint(payload, 210, 1))
    ident_active = bool(read_uint(payload, 211, 1))
    atc_services = bool(read_uint(payload, 212, 1))
    heading_type = "magnetic" if read_uint(payload, 213, 1) else "true"

    return {
        "emitter_category": emitter_category,
        "callsign": callsign,
        "squawk": squawk,
        "emergency": emergency,
        "uat_version": uat_version,
        "sil": sil,
        "transmit_mso": transmit_mso,
        "nac_p": nac_p,
        "nac_v": nac_v,
        "nic_baro": nic_baro,
        "has_cdti": has_cdti,
        "has_acas": has_acas,
        "acas_ra_active": acas_ra_active,
        "ident_active": ident_active,
        "atc_services": atc_services,
        "heading_type": heading_type,
    }

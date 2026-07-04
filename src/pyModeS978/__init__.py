from . import _aux_sv, _frame, _mode_status, _state_vector

__version__ = "9999.99.99"

_SV_TYPES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
_MS_TYPES = {1, 3}
_AUXSV_TYPES = {1, 2, 5, 6}


def decode(raw: str) -> dict | None:
    frame = _frame.parse(raw)
    if frame is None:
        return None

    result = {
        "direction": frame.direction,
        "payload_type": frame.payload_type,
        "address_qualifier": frame.address_qualifier,
        "icao": frame.icao,
    }

    payload_type = int(frame.payload_type)

    if payload_type in _SV_TYPES:
        result.update(_state_vector.decode(frame.payload, frame.address_qualifier))
    else:
        result.update(dict.fromkeys(_state_vector.FIELDS))

    if payload_type in _MS_TYPES:
        result.update(_mode_status.decode(frame.payload))
    else:
        result.update(dict.fromkeys(_mode_status.FIELDS))

    if payload_type in _AUXSV_TYPES:
        result.update(_aux_sv.decode(frame.payload))
    else:
        result.update(dict.fromkeys(_aux_sv.FIELDS))

    return result

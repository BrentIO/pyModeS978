from . import _aux_sv, _frame, _mode_status, _state_vector, _uncertainty
from ._enums import AltitudeSource
from ._version import __version__ as __version__

_SV_TYPES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
_MS_TYPES = {1, 3}
_AUXSV_TYPES = {1, 2, 5, 6}


def decode(raw: str) -> dict | None:
    frame = _frame.parse(raw)
    if frame is None:
        return None

    result = {
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
        result.update(
            _uncertainty.derive(
                nic=result["nic"],
                nic_supplement_a=result["nic_supplement_a"],
                nac_p=result["nac_p"],
                nac_v=result["nac_v"],
                sil=result["sil"],
            )
        )
    else:
        result.update(dict.fromkeys(_mode_status.FIELDS))
        result.update(dict.fromkeys(_uncertainty.FIELDS))

    if payload_type in _AUXSV_TYPES:
        result.update(_aux_sv.decode(frame.payload))
    else:
        result.update(dict.fromkeys(_aux_sv.FIELDS))

    if (
        result["altitude"] is not None
        and result["altitude_secondary"] is not None
        and result["altitude_type"] is not None
    ):
        if result["altitude_type"] == AltitudeSource.BARO:
            result["geo_minus_baro"] = result["altitude_secondary"] - result["altitude"]
        else:
            result["geo_minus_baro"] = result["altitude"] - result["altitude_secondary"]
    else:
        result["geo_minus_baro"] = None

    return dict(sorted(result.items()))

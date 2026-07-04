# pyModeS978

A pure-Python decoder for UAT (978 MHz) frames — the sibling protocol to 1090 MHz ADS-B. `pyModeS` has no UAT
support and no Python UAT decoder exists elsewhere, so this library implements the frame layout from scratch.

## Status

Core decoding (HDR, State Vector, Mode Status, AUX SV) is implemented. Test coverage against real-world
captures (#7/#8) and PyPI publishing (#9) are still open. See the
[issue tracker](https://github.com/BrentIO/pyModeS978/issues) for what's left.

## Install

```bash
pip install pyModeS978
```

## Usage

```python
import pyModeS978

result = pyModeS978.decode(raw)   # dict | None
```

`raw` is accepted with or without the dump978-fa direction prefix (`-` = downlink, `+` = uplink); trailing
`;metadata` is stripped if present. Uplink frames (FIS-B weather/NOTAM broadcasts, not traffic data) always
decode to `None` — see [#1](https://github.com/BrentIO/pyModeS978/issues/1) for why.

Fields not applicable to a given frame's `payload_type` are present with value `None`, never omitted. Real
example output (a long-frame ADS-B message: HDR + State Vector + Mode Status + AUX SV):

```python
{
    'direction': 'downlink',
    'payload_type': PayloadType.LONG,
    'address_qualifier': AddressQualifier.ADSB_ICAO,
    'icao': 'A042FF',
    'latitude': 28.078308,
    'longitude': -81.592412,
    'altitude': 34875,
    'altitude_type': 'baro',
    'nic': 9,
    'airground_state': 'airborne',
    'groundspeed': 486,
    'track': 357,
    'track_type': 'track',
    'vertical_rate': 832,
    'vertical_rate_source': 'baro',
    'length': None,
    'width': None,
    'position_offset': None,
    'utc_coupled': True,
    'tisb_site_id': None,
    'emitter_category': EmitterCategory.MEDIUM,
    'callsign': 'N116FE',
    'squawk': None,
    'emergency': Emergency.NO_EMERGENCY,
    'uat_version': 2,
    'sil': 3,
    'transmit_mso': 35,
    'nac_p': 10,
    'nac_v': 2,
    'nic_baro': True,
    'has_cdti': True,
    'has_acas': True,
    'acas_ra_active': True,
    'ident_active': False,
    'atc_services': False,
    'heading_type': 'true',
    'altitude_secondary': 37050,
    'altitude_secondary_type': 'geo',
}
```

`payload_type`, `address_qualifier`, `emitter_category`, and `emergency` are `IntEnum`s (still compare/hash
equal to their plain-int value) with a fallback to the plain int for any raw value that isn't a named member.

## License

MIT — see [LICENSE](LICENSE).

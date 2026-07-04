# pyModeS978

A pure-Python decoder for UAT (978 MHz) frames — the sibling protocol to 1090 MHz ADS-B. `pyModeS` has no UAT
support and no Python UAT decoder exists elsewhere, so this library implements the frame layout from scratch.

## Status

Under active development — the public API below is not implemented yet (tracked in
[#4](https://github.com/BrentIO/pyModeS978/issues/4)–[#6](https://github.com/BrentIO/pyModeS978/issues/6)).
Not yet published to PyPI.

## Install

```bash
pip install pyModeS978
```

## Usage

```python
import pyModeS978

result = pyModeS978.decode(raw)   # dict | None
# {
#   'payload_type': 1,
#   'address_qualifier': 0,
#   'icao': '28C4F1',
#   'latitude': 33.6423,
#   'longitude': -84.4210,
#   'altitude': 37000,
#   'altitude_type': 'baro',
#   'nic': 8,
#   'airground_state': 'airborne',
#   'groundspeed': 447,
#   'track': 271.4,
#   'vertical_rate': -640,
#   'callsign': 'DAL2',
#   'squawk': None,
#   'emitter_category': 'A3',
#   'emergency': None,
#   'direction': 'downlink',
# }
```

`raw` is accepted with or without the dump978-fa direction prefix (`-` = downlink, `+` = uplink); trailing
`;metadata` is stripped if present. Uplink frames (FIS-B weather/NOTAM broadcasts, not traffic data) always
decode to `None` — see [#1](https://github.com/BrentIO/pyModeS978/issues/1) for why.

## License

MIT — see [LICENSE](LICENSE).

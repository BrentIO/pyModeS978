# pyModeS978

A pure-Python decoder for UAT (978 MHz) frames — the sibling protocol to 1090 MHz ADS-B. `pyModeS` has no UAT
support and no Python UAT decoder exists elsewhere, so this library implements the frame layout from scratch.

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

Fields not applicable to a given frame's `payload_type` are present with value `None`, never omitted. Keys are
sorted alphabetically, so a specific field is easy to find in printed output. Real example output (a
long-frame ADS-B message: HDR + State Vector + Mode Status + AUX SV):

```python
{
    'address_qualifier': AddressQualifier.ADSB_ICAO,
    'airground_state': 'airborne',
    'altitude': 34875,
    'altitude_secondary': 37050,
    'altitude_secondary_type': 'GNSS',
    'altitude_type': 'BARO',
    'atc_services': False,
    'callsign': 'N116FE',
    'category': EmitterCategory.MEDIUM,
    'direction': 'downlink',
    'emergency': Emergency.NO_EMERGENCY,
    'es_in': True,
    'groundspeed': 486,
    'gva': 2,
    'heading': None,
    'heading_type': None,
    'icao': 'A042FF',
    'ident_active': False,
    'latitude': 28.078308,
    'length': None,
    'longitude': -81.592412,
    'nac_p': 10,
    'nac_v': 2,
    'nic': 9,
    'nic_baro': True,
    'nic_supplement_a': False,
    'payload_type': PayloadType.LONG,
    'position_accuracy_epu_m': 10,
    'position_accuracy_vepu_m': 15,
    'position_containment_radius_m': None,
    'position_offset': None,
    'position_vpl_m': None,
    'sda': 2,
    'sil': 3,
    'sil_probability_horizontal': 1e-07,
    'sil_probability_vertical': 2e-07,
    'sil_supplement': SILSupplement.PER_HOUR,
    'single_antenna': False,
    'squawk': None,
    'tcas_operational': True,
    'tcas_ra_active': False,
    'tisb_site_id': None,
    'track': 357.3,
    'transmit_mso': 35,
    'uat_in': True,
    'utc_coupled': True,
    'velocity_accuracy_hfom_ms': 3,
    'velocity_accuracy_vfom_ms': 4.5,
    'version': 2,
    'vertical_rate': 832,
    'vr_source': 'BARO',
    'width': None,
}
```

`position_containment_radius_m`/`position_vpl_m` are `None` here because `nic=9` is only resolvable when
`nic_supplement_a=True` — a real, expected gap in the underlying table, not a bug (see `_uncertainty.py`).

`payload_type`, `address_qualifier`, `category`, `emergency`, and `sil_supplement` are `IntEnum`s (still
compare/hash equal to their plain-int value) with a fallback to the plain int for any raw value that isn't a
named member.

## Versioning & releases

Versions are calendar-based, `YYYY.M.b` (year, month, per-month release count — no leading zeros, e.g.
`2026.7.1`), matching the convention used across other BrentIO repos. The version isn't stored in a source
file at all: `pyproject.toml` declares it `dynamic`, and [`hatch-vcs`](https://github.com/ofek/hatch-vcs)
derives it from the git tag at build time. An untagged install (e.g. straight off `main`) falls back to a
`0.1.devN+g<hash>` style dev version.

Releases are cut via the **🚀 Release** GitHub Actions workflow (`workflow_dispatch`, takes a `version` input
matching the format above), which validates the version, tags `main`, and creates a GitHub Release.

## License

MIT — see [LICENSE](LICENSE).

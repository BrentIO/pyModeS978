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
    'airground_state': AirgroundState.AIRBORNE_SUBSONIC,
    'altitude': 34875,
    'altitude_secondary': 37050,
    'altitude_secondary_type': AltitudeSource.GNSS,
    'altitude_type': AltitudeSource.BARO,
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
    'vr_source': AltitudeSource.BARO,
    'width': None,
}
```

`position_containment_radius_m`/`position_vpl_m` are `None` here because `nic=9` is only resolvable when
`nic_supplement_a=True` — a real, expected gap in the underlying table, not a bug (see `_uncertainty.py`).

`payload_type`, `address_qualifier`, `category`, `emergency`, `sil_supplement`, `airground_state`,
`altitude_type`, `altitude_secondary_type`, `vr_source`, and `heading_type` are all `IntEnum`s (still
compare/hash equal to their plain-int value). `payload_type`/`address_qualifier`/`category`/`emergency`/
`sil_supplement` fall back to the plain int for any raw value with no named member; the other five have every
raw value named, so no fallback applies. `airground_state` does not collapse subsonic/supersonic airborne into
one value -- `AirgroundState.AIRBORNE_SUBSONIC` and `AirgroundState.AIRBORNE_SUPERSONIC` are distinct members,
so collapse them yourself if you don't care about the distinction. `altitude_type`, `altitude_secondary_type`,
and `vr_source` all share the same `AltitudeSource` enum (`BARO`/`GNSS`).

## Data dictionary

Every field `decode()` can return, grouped by the frame block it comes from. Fields not applicable to a given
frame's `payload_type` are `None`, never omitted — each section below states which payload types it applies to.

### HDR (all payload types)

| Field | Type | Meaning |
|---|---|---|
| `direction` | `str` | `"downlink"` or `"uplink"`. Always `"downlink"` in practice — uplink frames (FIS-B weather/NOTAM broadcasts, not traffic) return `None` from `decode()` before this field is ever set. |
| `payload_type` | `PayloadType` | UAT payload type, 5-bit raw. Determines which of the blocks below are present in this frame. Not every raw value is named; unnamed values fall back to the plain int. |
| `address_qualifier` | `AddressQualifier` | What kind of address `icao` is: native ADS-B ICAO, TIS-B (ICAO or non-ICAO), surface vehicle, fixed beacon, etc. |
| `icao` | `str` | 24-bit address, 6 hex chars, uppercase. Despite the name, not always a real ICAO address — see `address_qualifier`. |

### State Vector (payload types 0–10)

| Field | Type | Meaning |
|---|---|---|
| `latitude` | `float \| None` | Decoded position, 6 decimal places. Absolute in every frame — no CPR even/odd pairing needed, unlike 1090. `None` if there's no valid fix (`nic == 0` and raw lat/lon both `0`). |
| `longitude` | `float \| None` | See `latitude`. |
| `altitude` | `int \| None` | Feet. `None` if unavailable. |
| `altitude_type` | `AltitudeSource \| None` | `BARO` or `GNSS` — which kind of altitude `altitude` is. `None` alongside `altitude` when unavailable. |
| `nic` | `int` (0–15) | Navigation Integrity Category — confidence in the position fix. Combines with Mode Status's `nic_supplement_a` to resolve `position_containment_radius_m`/`position_vpl_m` below; not every combination is defined. |
| `airground_state` | `AirgroundState` | `AIRBORNE_SUBSONIC`, `AIRBORNE_SUPERSONIC`, `ON_GROUND`, or `RESERVED`. Subsonic/supersonic are kept distinct, not collapsed — fold them together yourself if you don't need the distinction. |
| `groundspeed` | `int \| None` | Knots, rounded. `None` for `RESERVED`. |
| `track` | `float \| None` | Track over ground, 1 decimal. Airborne: always this field (never `heading`). Ground: only when the frame's type code says "track" rather than heading. |
| `heading` | `float \| None` | Ground-only. Populated instead of `track` when the type code says magnetic or true heading — see `heading_type`. |
| `heading_type` | `HeadingType \| None` | `MAGNETIC` or `TRUE` — which kind of heading `heading` is. `None` whenever `heading` is `None`. |
| `vertical_rate` | `int \| None` | Feet/min, signed. Airborne only — `None` on the ground (those bits hold aircraft dimensions instead). |
| `vr_source` | `AltitudeSource \| None` | `BARO` or `GNSS` — which kind of altitude `vertical_rate` is derived from. |
| `length` | `int \| None` | Aircraft length, meters. Ground-only. |
| `width` | `float \| None` | Aircraft width, meters. Ground-only. |
| `position_offset` | `bool \| None` | Whether the GPS antenna is offset from the nose/wingtip, per the length/width code's convention. Ground-only. |
| `utc_coupled` | `bool \| None` | Whether the frame's time reference is UTC-coupled. Native ADS-B (`address_qualifier` not TIS-B) only. |
| `tisb_site_id` | `int \| None` | Ground station site ID. TIS-B frames only — same 4 raw bits as `utc_coupled`, reinterpreted per `address_qualifier`. |

### Mode Status (payload types 1, 3)

| Field | Type | Meaning |
|---|---|---|
| `category` | `EmitterCategory` | Aircraft/vehicle emitter category, 40 raw values (most are `RESERVED_n`). |
| `callsign` | `str \| None` | Flight ID, base-40-decoded and whitespace-stripped. `None` if this frame's field holds a squawk instead, or is blank. |
| `squawk` | `str \| None` | Mode 3/A squawk code. A CSID flag in the same raw bits picks whether this field is a callsign or a squawk — UAT has no DF 5/21 equivalent, so this is the *only* source of squawk. Mutually exclusive with `callsign`. |
| `emergency` | `Emergency` | Emergency/priority status. |
| `version` | `int` | ADS-B/MOPS version the transmitting equipment implements. |
| `sil` | `int` (0–3) | Source Integrity Level — probability the reported position exceeds the NIC containment radius without alerting. Combines with `sil_supplement` and `nic` to resolve the Derived probabilities below. |
| `transmit_mso` | `int` | Message Start Opportunity slot the transmitter used — a radio-layer detail, not aircraft state. |
| `sda` | `int` (0–3) | System Design Assurance — failure-rate classification of the transmitting equipment. |
| `nac_p` | `int` (0–15 raw; only 0–11 are defined) | Navigation Accuracy Category for Position. Resolves `position_accuracy_epu_m`/`position_accuracy_vepu_m` below — undefined raw values (12–15) resolve those to `None`. |
| `nac_v` | `int` (0–7 raw; only 0–4 are defined) | Navigation Accuracy Category for Velocity. Resolves `velocity_accuracy_hfom_ms`/`velocity_accuracy_vfom_ms` below — undefined raw values (5–7) resolve those to `None`. |
| `nic_baro` | `bool` | Whether the barometric altitude has been cross-checked against another source. |
| `uat_in` | `bool` | Capability code: has a UAT receiver. |
| `es_in` | `bool` | Capability code: has a 1090ES receiver. |
| `tcas_operational` | `bool` | Capability code: TCAS/ACAS is installed and operational. |
| `tcas_ra_active` | `bool` | Operational mode: a TCAS/ACAS resolution advisory is currently active. |
| `ident_active` | `bool` | Operational mode: the pilot has pressed IDENT. |
| `atc_services` | `bool` | Operational mode: aircraft is receiving ATC services. |
| `sil_supplement` | `SILSupplement` | `PER_HOUR` or `PER_SAMPLE` — the time base `sil`'s probabilities apply to, not a different probability table. |
| `gva` | `int` (0–3) | Geometric Vertical Accuracy — 95% accuracy bound on GNSS altitude. |
| `single_antenna` | `bool` | Whether the transmitter uses a single antenna (vs. antenna diversity). |
| `nic_supplement_a` | `bool` | The one NIC supplement bit UAT has (1090 has two — see `_uncertainty.py`). Combines with `nic` to resolve `position_containment_radius_m`/`position_vpl_m` below. |

### AUX SV (payload types 1, 2, 5, 6)

| Field | Type | Meaning |
|---|---|---|
| `altitude_secondary` | `int \| None` | Feet. Whichever altitude type State Vector's `altitude` *isn't* — if `altitude_type` is `BARO`, this is the GNSS altitude, and vice versa. |
| `altitude_secondary_type` | `AltitudeSource \| None` | `BARO` or `GNSS` — always the opposite of `altitude_type`. |

### Derived (present whenever Mode Status is)

Not decoded from raw bits directly — derived from `nac_p`/`nac_v`/`sil`/`nic`/`nic_supplement_a` via lookup
tables ported from pyModeS's own `_uncertainty.py`. pyModeS keeps the equivalent tables to itself and leaves
resolving them to the caller; `decode()` resolves them automatically since it's a single call.

| Field | Type | Meaning |
|---|---|---|
| `position_accuracy_epu_m` | `float \| None` | Estimated Position Uncertainty, meters (95%), from `nac_p`. |
| `position_accuracy_vepu_m` | `float \| None` | Vertical EPU, meters (95%), from `nac_p`. Only defined for the two highest `nac_p` values. |
| `velocity_accuracy_hfom_ms` | `float \| None` | Horizontal Figure of Merit for velocity, m/s, from `nac_v`. |
| `velocity_accuracy_vfom_ms` | `float \| None` | Vertical Figure of Merit for velocity, m/s, from `nac_v`. |
| `position_containment_radius_m` | `float \| None` | Containment radius implied by `nic` + `nic_supplement_a`. `None` for combinations the spec doesn't define (e.g. `nic=9` is only defined when `nic_supplement_a=True`) — a real gap in the table, not a bug. |
| `position_vpl_m` | `float \| None` | Vertical Protection Limit implied by `nic` + `nic_supplement_a`. Same undefined-combination caveat as `position_containment_radius_m`. |
| `sil_probability_horizontal` | `float \| None` | Probability `position_containment_radius_m` is exceeded without alerting, from `sil`. Time base given by `sil_supplement`. |
| `sil_probability_vertical` | `float \| None` | Probability `position_vpl_m` is exceeded without alerting, from `sil`. Same time-base caveat. |

### Comparison with pyModeS (1090)

Where a pyModeS978 field has a real pyModeS equivalent, here's how they compare:

| pyModeS (1090) | pyModeS978 (978) | Note |
|---|---|---|
| `icao` | `icao` | Same. |
| `latitude`/`longitude` | `latitude`/`longitude` | Same concept; UAT never needs CPR pairing (see above), 1090 does. |
| `altitude` | `altitude` | Same. |
| — | `altitude_type` | No 1090 equivalent — pyModeS infers baro-vs-GNSS from the raw ADS-B typecode rather than exposing it as its own field. |
| `squawk` | `squawk` | Same. |
| `callsign` | `callsign` | Same. |
| `category` (bare `int`) | `category` (`EmitterCategory`) | Same concept; pyModeS never named these values, we did — this was true before #29 too, so it was never actually a pyModeS-parity decision. |
| `groundspeed` | `groundspeed` | Same. |
| `track` | `track` | Same. |
| `heading` | `heading` | Same field name, different reason for existing: pyModeS's is from a distinct BDS 0,9 velocity subtype; ours is airborne/ground-dependent (see State Vector table above). |
| — | `heading_type` | No 1090 equivalent — added to preserve the magnetic/true distinction UAT's ground-heading type code carries. |
| `vertical_rate` | `vertical_rate` | Same. |
| `vr_source` (bare `str`) | `vr_source` (`AltitudeSource`) | Same values (`"BARO"`/`"GNSS"` in pyModeS, matched exactly), enum instead of bare string. |
| `nac_v` | `nac_v` | Same. |
| `nac_p` | `nac_p` | Same. |
| `version` | `version` | Same. |
| `sil` | `sil` | Same. |
| `sil_supplement` (bare `int`) | `sil_supplement` (`SILSupplement`) | Same concept, enum instead of bare int. |
| `nic_baro` (bare `int`) | `nic_baro` (`bool`) | Same concept; pyModeS exposes the raw 0/1 int, we expose it as a `bool`. |
| `nic_supplement_a` (bare `int`) | `nic_supplement_a` (`bool`) | Same concept; same bare-int-vs-`bool` difference as `nic_baro`. Name matches pyModeS's exactly (see #29). |
| `capability_class`/`operational_mode` (raw bitfield `int`s) | `uat_in`/`es_in`/`tcas_operational`/`tcas_ra_active`/`ident_active`/`atc_services` | pyModeS exposes these two 1090 bitfields as raw ints without further decoding; we break the UAT equivalent out into individual named booleans. |
| `emergency_state` (bare `int`) | `emergency` (`Emergency`) | Different field name (not aligned — flagged here, not renamed; renames are out of scope for this issue) as well as bare-int-vs-enum. |
| `geo_minus_baro` (a delta) | `altitude_secondary` (an absolute altitude) | Different representation of a similar idea: 1090 gives you the difference between geometric and barometric altitude; UAT's AUX SV gives you the second altitude's actual value directly. |
| — | `address_qualifier`, `payload_type`, `direction`, `airground_state`, `gva`, `sda`, `transmit_mso`, `single_antenna`, `length`, `width`, `position_offset`, `utc_coupled`, `tisb_site_id`, `altitude_secondary_type`, all eight Derived fields | UAT-specific or UAT-derived, no 1090 equivalent. |

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

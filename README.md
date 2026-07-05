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

Every field `decode()` can return, alphabetical by field name. **pyModeS Equivalent** is the matching field in
pyModeS's 1090 `decode()` output, or ❌ if 1090 has nothing comparable. Two recurring ❌ patterns, noted once
here instead of in every row: pyModeS exposes its Mode Status-equivalent capability/operational-mode bits as
two raw bitfield ints (`capability_class`, `operational_mode`) rather than breaking them out into named
booleans the way `uat_in`/`es_in`/`tcas_operational`/`tcas_ra_active`/`ident_active`/`atc_services` do; and
pyModeS keeps its own uncertainty lookup tables (`_uncertainty.py`) to itself rather than auto-populating
`decode()` output with them, unlike the `position_accuracy_*`/`velocity_accuracy_*`/`position_containment_*`/
`sil_probability_*` fields here.

| Field | pyModeS Equivalent | Description | Requirements |
|---|---|---|---|
| `address_qualifier` | ❌ | `AddressQualifier` enum — what kind of address `icao` is and where the frame came from: native ADS-B ICAO, TIS-B (ICAO or non-ICAO), surface vehicle, fixed beacon, etc. | All payload types (HDR). |
| `airground_state` | ❌ | `AirgroundState` enum — `AIRBORNE_SUBSONIC`, `AIRBORNE_SUPERSONIC`, `ON_GROUND`, or `RESERVED`. Subsonic/supersonic kept distinct, not collapsed into one `AIRBORNE` value. | Payload types 0–10 (State Vector). |
| `altitude` | `altitude` | Feet, from the 12-bit raw altitude code: `(raw - 1) * 25 - 1000`. | Payload types 0–10; `None` if the raw altitude code is `0` (unavailable). |
| `altitude_secondary` | ❌ (pyModeS's `geo_minus_baro` is a *delta* between the two altitudes, not a second absolute value) | Feet. Whichever altitude type `altitude` *isn't* — if `altitude_type` is `BARO`, this is the GNSS altitude, and vice versa. | Payload types 1, 2, 5, 6 (AUX SV); `None` if the raw AUX SV altitude code is `0`. |
| `altitude_secondary_type` | ❌ | `AltitudeSource` enum (`BARO`/`GNSS`) — always the opposite of `altitude_type`. | Same as `altitude_secondary`. |
| `altitude_type` | ❌ (pyModeS infers baro-vs-GNSS from the raw ADS-B typecode instead of exposing a field) | `AltitudeSource` enum (`BARO`/`GNSS`) — which kind of altitude `altitude` is. | Payload types 0–10; `None` alongside `altitude` when unavailable. |
| `atc_services` | ❌ (`operational_mode` bitfield, see above) | Operational mode bit — aircraft is receiving ATC services. | Payload types 1, 3 (Mode Status). |
| `callsign` | `callsign` | Flight ID, base-40-decoded from Mode Status's packed character field and whitespace-stripped. | Payload types 1, 3; `None` if this frame's field holds a squawk instead (see `squawk`), or is blank. |
| `category` | `category` (bare `int`; ours is `EmitterCategory`) | Aircraft/vehicle emitter category, 40 raw values (most are `RESERVED_n`). pyModeS never named these values — a deviation from pyModeS predating any parity effort, not a #29 decision. | Payload types 1, 3. |
| `direction` | ❌ | `"downlink"` or `"uplink"`. | All payload types; always `"downlink"` in practice since uplink frames return `None` from `decode()` before this field is ever set. |
| `emergency` | `emergency_state` (bare `int`) | `Emergency` enum — emergency/priority status. Name intentionally left unaligned with pyModeS's `emergency_state` — flagged here, not renamed (renames are out of scope for this dictionary). | Payload types 1, 3. |
| `es_in` | ❌ (`capability_class` bitfield, see above) | Capability code — has a 1090ES receiver. | Payload types 1, 3. |
| `groundspeed` | `groundspeed` | Knots, rounded. Airborne: `√(ns² + ew²)` from the N/S and E/W velocity components. Ground: a direct raw code. | Payload types 0–10; `None` for `RESERVED` airground state. |
| `gva` | ❌ | Geometric Vertical Accuracy, 2-bit raw (0–3) — 95% accuracy bound on GNSS altitude. | Payload types 1, 3. |
| `heading` | `heading` | Ground-only heading, 1 decimal, from the 11-bit raw track/heading code (`* 360/512`). | Payload types 0–10; populated instead of `track` only when the ground type code says magnetic or true heading — see `heading_type`. |
| `heading_type` | ❌ (no 1090 equivalent — added to preserve the magnetic/true distinction UAT's ground type code carries) | `HeadingType` enum (`MAGNETIC`/`TRUE`) — which kind of heading `heading` is. | Payload types 0–10; `None` whenever `heading` is `None`. |
| `icao` | `icao` | 24-bit address, 6 hex chars, uppercase. | All payload types; despite the name, not always a real ICAO address — see `address_qualifier`. |
| `ident_active` | ❌ (`operational_mode` bitfield, see above) | Operational mode bit — the pilot has pressed IDENT. | Payload types 1, 3. |
| `latitude` | `latitude` | Decoded position, 6 decimal places (`raw * 360 / 2^24`). Absolute in every frame — no CPR even/odd pairing needed, unlike 1090. | Payload types 0–10; `None` if there's no valid fix (`nic == 0` and raw lat/lon both `0`). |
| `length` | ❌ | Aircraft length, meters, from the width/length code table. | Payload types 0–10; ground only. |
| `longitude` | `longitude` | See `latitude`. | Same as `latitude`. |
| `nac_p` | `nac_p` | Navigation Accuracy Category for Position, 4-bit raw (0–15; only 0–11 defined). Resolves `position_accuracy_epu_m`/`position_accuracy_vepu_m`. | Payload types 1, 3. |
| `nac_v` | `nac_v` | Navigation Accuracy Category for Velocity, 3-bit raw (0–7; only 0–4 defined). Resolves `velocity_accuracy_hfom_ms`/`velocity_accuracy_vfom_ms`. | Payload types 1, 3. |
| `nic` | ❌ (pyModeS resolves NIC internally from typecode + supplement bits for its own uncertainty functions, but never exposes the resolved number as a `decode()` output key) | Navigation Integrity Category, 4-bit raw (0–15) — confidence in the position fix. Combines with `nic_supplement_a` to resolve `position_containment_radius_m`/`position_vpl_m`. | Payload types 0–10. |
| `nic_baro` | `nic_baro` (bare `int`; ours is `bool`) | Whether the barometric altitude has been cross-checked against another source. | Payload types 1, 3. |
| `nic_supplement_a` | `nic_supplement_a` (bare `int`; ours is `bool`; name matches pyModeS exactly — see #29) | The one NIC supplement bit UAT has (1090 has two). | Payload types 1, 3. |
| `payload_type` | ❌ | `PayloadType` enum, 5-bit raw — determines which blocks (State Vector/Mode Status/AUX SV) are present in this frame. | All payload types. |
| `position_accuracy_epu_m` | ❌ (see above) | Estimated Position Uncertainty, meters (95%), from `nac_p`. | Payload types 1, 3. |
| `position_accuracy_vepu_m` | ❌ (see above) | Vertical EPU, meters (95%), from `nac_p`. Only defined for the two highest `nac_p` values. | Payload types 1, 3. |
| `position_containment_radius_m` | ❌ (see above) | Containment radius implied by `nic` + `nic_supplement_a`. `None` for combinations the spec doesn't define (e.g. `nic=9` is only defined when `nic_supplement_a=True`) — a real gap in the table, not a bug. | Payload types 1, 3. |
| `position_offset` | ❌ | Whether the GPS antenna is offset from the nose/wingtip, per the length/width code's convention. | Payload types 0–10; ground only. |
| `position_vpl_m` | ❌ (see above) | Vertical Protection Limit implied by `nic` + `nic_supplement_a`. Same undefined-combination caveat as `position_containment_radius_m`. | Payload types 1, 3. |
| `sda` | ❌ | System Design Assurance, 2-bit raw (0–3) — failure-rate classification of the transmitting equipment. | Payload types 1, 3. |
| `sil` | `sil` | Source Integrity Level, 2-bit raw (0–3) — probability the reported position exceeds the NIC containment radius without alerting. | Payload types 1, 3. |
| `sil_probability_horizontal` | ❌ (see above) | Probability `position_containment_radius_m` is exceeded without alerting, from `sil`. Time base given by `sil_supplement`. | Payload types 1, 3. |
| `sil_probability_vertical` | ❌ (see above) | Probability `position_vpl_m` is exceeded without alerting, from `sil`. Same time-base caveat. | Payload types 1, 3. |
| `sil_supplement` | `sil_supplement` (bare `int`; ours is `SILSupplement`) | `PER_HOUR` or `PER_SAMPLE` — the time base `sil`'s probabilities apply to, not a different probability table. | Payload types 1, 3. |
| `single_antenna` | ❌ | Whether the transmitter uses a single antenna (vs. antenna diversity). | Payload types 1, 3. |
| `squawk` | `squawk` | Mode 3/A squawk code. A CSID flag in the same raw bits as `callsign` picks whether this field is a callsign or a squawk — UAT has no DF 5/21 equivalent, so this is the *only* source of squawk. | Payload types 1, 3; mutually exclusive with `callsign`. |
| `tcas_operational` | `tcas_operational` (`capability_class` bitfield in pyModeS, exposed there as its own top-level key too) | Capability code — TCAS/ACAS is installed and operational. | Payload types 1, 3. |
| `tcas_ra_active` | ❌ (1090's closest concept is the multi-field BDS 3,0 ACAS RA broadcast — `issued_ra`, `corrective`, etc. — not a single boolean) | Operational mode bit — a TCAS/ACAS resolution advisory is currently active. | Payload types 1, 3. |
| `tisb_site_id` | ❌ | Ground station site ID. | Payload types 0–10; TIS-B frames only — same 4 raw bits as `utc_coupled`, reinterpreted per `address_qualifier`. |
| `track` | `track` | Track over ground, 1 decimal. Airborne: `atan2` of the N/S and E/W velocity components. Ground: a direct raw code. | Payload types 0–10; airborne: always this field (never `heading`); ground: only when the type code says "track" rather than heading. |
| `transmit_mso` | ❌ | Message Start Opportunity slot the transmitter used — a radio-layer detail, not aircraft state. | Payload types 1, 3. |
| `uat_in` | ❌ (`capability_class` bitfield, see above) | Capability code — has a UAT receiver. | Payload types 1, 3. |
| `utc_coupled` | ❌ | Whether the frame's time reference is UTC-coupled. | Payload types 0–10; native ADS-B (non-TIS-B `address_qualifier`) only. |
| `velocity_accuracy_hfom_ms` | ❌ (see above) | Horizontal Figure of Merit for velocity, m/s, from `nac_v`. | Payload types 1, 3. |
| `velocity_accuracy_vfom_ms` | ❌ (see above) | Vertical Figure of Merit for velocity, m/s, from `nac_v`. | Payload types 1, 3. |
| `version` | `version` | ADS-B/MOPS version the transmitting equipment implements, 3-bit raw. | Payload types 1, 3. |
| `vertical_rate` | `vertical_rate` | Feet/min, signed, from the 11-bit raw vertical rate code. | Payload types 0–10; airborne only — `None` on the ground (those bits hold aircraft dimensions instead). |
| `vr_source` | `vr_source` (bare `str`; ours is `AltitudeSource`) | `BARO` or `GNSS` — which kind of altitude `vertical_rate` is derived from. Same values as pyModeS's own `"BARO"`/`"GNSS"` strings, matched exactly. | Payload types 0–10; airborne only. |
| `width` | ❌ | Aircraft width, meters, from the width/length code table. | Payload types 0–10; ground only. |

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

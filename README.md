# pyModeS978

A pure-Python decoder for UAT (978 MHz) frames — the sibling protocol to 1090 MHz ADS-B. This project builds
on the excellent work of [`pyModeS`](https://github.com/junzis/pyModeS), the Python library this one takes its
name, API shape, and field-naming conventions from. pyModeS has no UAT support and no Python UAT decoder
exists elsewhere, so this library implements the frame layout from scratch. Wherever possible, fields with
like-for-like meaning are mapped 1:1, so using this library should feel familiar — often a drop-in
replacement — for anyone already working with pyModeS.

## Install

```bash
pip install pyModeS978
```

## Usage

```python
import pyModeS978

raw = "-08A042FF27EF018BF51C59C9079A0C40EB1019073F5D440B8EA5E280005F30000000"
result = pyModeS978.decode(raw)   # dict | None
```

`raw` is accepted with or without the dump978-fa direction prefix (`-` = downlink, `+` = uplink); trailing
`;metadata` is stripped if present. If the prefix is omitted, direction is inferred from byte length instead.
Uplink frames (FIS-B weather/NOTAM ground broadcasts) always decode to `None` — they carry no traffic data,
and 1090 traffic rebroadcast to UAT receivers (TIS-B/ADS-R) already arrives as a downlink frame, distinguished
via `address_qualifier`. `None` here is expected behavior, not an error — see [Error Handling](#error-handling)
for what actually raises.

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
    'emergency_state': Emergency.NO_EMERGENCY,
    'es_in': True,
    'geo_minus_baro': 2175,
    'groundspeed': 486,
    'gva': 2,
    'heading': None,
    'heading_type': None,
    'icao': 'A042FF',
    'ident_active': False,
    'latitude': 28.078308,
    'length': None,
    'longitude': -81.592412,
    'magnetic_heading': None,
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
    'vertical_status': 'airborne',
    'vr_source': AltitudeSource.BARO,
    'width': None,
}
```

`position_containment_radius_m`/`position_vpl_m` are `None` here because `nic=9` is only resolvable when
`nic_supplement_a=True` — a real, expected gap in the underlying table, not a bug (see `_uncertainty.py`).

Fields typed as one of pyModeS978's `IntEnum`s (see the data dictionary for the complete list, their values,
and any per-field caveats) still compare/hash equal to their plain-int value.

## Error Handling

Malformed input to `decode()` raises one of three `DecodeError` subclasses, rather than returning `None`.
`None` is reserved for uplink frames (see [Usage](#usage)). `DecodeError` itself subclasses `ValueError`, so
`except ValueError:` catches any of them:

- `InvalidHexError`: the input contains non-hex characters, or an odd number of hex characters.
- `InvalidLengthError`: the decoded input isn't 18, 34, or 432 bytes.
- `DirectionMismatchError`: the `-`/`+` prefix disagrees with the direction implied by the input's byte length.

Every error type carries the original input passed to `decode()` as `.raw`, unmodified. This is useful for
correlating a failure back to its input.

## Data dictionary

The table below lists every field either library can return, alphabetical by field name:

- **pyModeS978 Field** — the field pyModeS978 returns. `❌` means that data simply isn't available from a UAT
  frame.
- **pyModeS Equivalent** — the matching field in pyModeS's 1090 `decode()` output. `❌` means the reverse —
  1090 has nothing directly comparable.
- **Payload Types** — which `payload_type` values a field's block is structurally present for. `—` for
  pyModeS-only fields, since they don't exist in `decode()`'s output at all.
- **Notes** — everything else: finer per-frame conditions like ground/airborne-only, or when a field resolves
  to `None` even within an applicable payload type.

pyModeS-only fields are inserted alphabetically as if pyModeS978 had a field of that same name, so the whole
table reads as one merged, alphabetical list rather than "pyModeS978's first, then pyModeS's." Where a field's
type is one of pyModeS978's `IntEnum`s, its possible values are listed.

Two recurring patterns, noted once here instead of in every row:

- pyModeS exposes its Mode Status-equivalent capability/operational-mode bits as two raw bitfield ints
  (`capability_class`, `operational_mode`). UAT's smaller capability/operational-mode set made it practical to
  break these out into individual named booleans instead (`uat_in`, `es_in`, `tcas_operational`,
  `tcas_ra_active`, `ident_active`, `atc_services`).
- pyModeS's own `_uncertainty.py` has equivalent NIC/NACp/NACv/SIL lookup tables, but leaves calling them up
  to the caller. The `position_accuracy_*`/`velocity_accuracy_*`/`position_containment_*`/`sil_probability_*`
  fields here call the UAT equivalents automatically as part of `decode()`, since a single-call decode was
  the natural fit for how UAT frames are structured.

| pyModeS978 Field | pyModeS Equivalent | Description | Payload Types | Notes |
|---|---|---|---|---|
| ❌ | `acas_hybrid_surveillance` | ACAS hybrid surveillance capability flag. | — | 1090 only, BDS 1,0. |
| ❌ | `acas_operational` | Whether ACAS is operational (the data link capability report's own copy of this flag). | — | 1090 only, BDS 1,0. |
| ❌ | `acas_resolution_advisory` | Whether ACAS resolution advisory generation is active. | — | 1090 only, BDS 1,0. |
| ❌ | `acas_rtca_version` | Which RTCA ACAS version the equipment implements. | — | 1090 only, BDS 1,0. |
| `address_qualifier` | ❌ | `AddressQualifier` enum — what kind of address `icao` is and where the frame came from. Values: `ADSB_ICAO`, `NATIONAL_RESERVED`, `TISB_ICAO`, `TISB_OTHER`, `VEHICLE`, `FIXED_BEACON`, `RESERVED_6`, `RESERVED_7`. | All | — |
| ❌ | `aircraft_identification_capability` | Whether the transponder can report aircraft identification (BDS 0,8). | — | 1090 only, BDS 1,0. |
| `airground_state` | ❌ | `AirgroundState` enum — `AIRBORNE_SUBSONIC`, `AIRBORNE_SUPERSONIC`, `ON_GROUND`, or `RESERVED`. | 0–10 | — |
| ❌ | `airspeed` | Air-referenced (not ground) speed, knots — an alternative to `groundspeed` for some subtypes. | — | 1090 only, BDS 0,9. |
| ❌ | `airspeed_type` | Whether `airspeed` is true or indicated airspeed. | — | 1090 only, BDS 0,9. |
| `altitude` | `altitude` | Feet, from the 12-bit raw altitude code: `(raw - 1) * 25 - 1000`. | 0–10 | `None` if the raw altitude code is `0` (unavailable). |
| ❌ | `altitude_crossing` | Whether the RA commands an altitude crossing maneuver. | — | 1090 only, BDS 3,0. |
| ❌ | `altitude_hold_mode` | Whether altitude hold mode is engaged. | — | 1090 only, BDS 4,0. |
| `altitude_secondary` | ❌ | Feet. Whichever altitude type `altitude` *isn't* — if `altitude_type` is `BARO`, this is the GNSS altitude, and vice versa. | 1, 2, 5, 6 | pyModeS's `geo_minus_baro` is a *delta* between the two altitudes, not a second absolute value — see `geo_minus_baro` below for the delta itself. `None` if the raw AUX SV altitude code is `0`. |
| `altitude_secondary_type` | ❌ | `AltitudeSource` enum (`BARO`/`GNSS`) — always the opposite of `altitude_type`. | 1, 2, 5, 6 | Same as `altitude_secondary`. |
| `altitude_type` | ❌ | `AltitudeSource` enum (`BARO`/`GNSS`) — which kind of altitude `altitude` is. | 0–10 | pyModeS infers baro-vs-GNSS from the raw ADS-B typecode instead of exposing a field. `None` alongside `altitude` when unavailable. |
| ❌ | `approach_mode` | Whether approach mode is engaged. | — | 1090 only, BDS 4,0. |
| `atc_services` | ❌ | Operational mode bit — aircraft is receiving ATC services. | 1, 3 | Packed into pyModeS's `operational_mode` bitfield, not individually named there. |
| ❌ | `autopilot` | Whether the autopilot is engaged. | — | 1090 only, BDS 6,2. |
| ❌ | `baro_pressure_setting` | The pilot's barometric pressure setting, millibars. | — | 1090 only, BDS 4,0. |
| ❌ | `baro_vertical_rate` | Barometric vertical rate, feet/min. | — | 1090 only, BDS 6,0. |
| ❌ | `bds` | Which BDS register a message decoded as (e.g. "05", "09"), resolved from `typecode`. | — | 1090 only, DF17/18. |
| ❌ | `bds_candidates` | When BDS is ambiguous from typecode alone, the list of registers it might be. | — | 1090 only, DF17/18. |
| `callsign` | `callsign` | Flight ID, base-40-decoded from Mode Status's packed character field and whitespace-stripped. | 1, 3 | `None` if this frame's field holds a squawk instead (see `squawk`), or is blank. |
| ❌ | `capability` | 3-bit capability field — transponder's Mode S capability level. | — | 1090 only, DF11. |
| ❌ | `capability_class` | Raw capability class bitfield — the packed equivalent of `uat_in`/`es_in`/`tcas_operational`, exposed here as individually named booleans instead. | — | 1090 only, BDS 6,5 operational status report. |
| ❌ | `capability_text` | Human-readable decode of `capability`. | — | 1090 only, DF11. |
| `category` | `category` | Aircraft/vehicle emitter category. Values: `NO_INFORMATION`, `LIGHT`, `MEDIUM`, `MEDIUM_LARGE`, `MEDIUM_LARGE_HIGH_VORTEX`, `HEAVY`, `HIGHLY_MANEUVERABLE`, `ROTORCRAFT`, `RESERVED_8`, `GLIDER_SAILPLANE`, `LIGHTER_THAN_AIR`, `PARACHUTIST_SKYDIVER`, `ULTRALIGHT_HANGGLIDER_PARAGLIDER`, `RESERVED_13`, `UAV`, `SPACE_TRANSATMOSPHERIC`, `RESERVED_16`, `EMERGENCY_VEHICLE`, `SERVICE_VEHICLE`, `POINT_OBSTACLE`, `CLUSTER_OBSTACLE`, `LINE_OBSTACLE`, `RESERVED_22`–`RESERVED_39`. | 1, 3 | pyModeS exposes this as a bare `int`; pyModeS978 names the values here for readability. |
| ❌ | `common_usage_gicb_capability` | Whether the transponder reports common-usage GICB capability (BDS 1,7). | — | 1090 only, BDS 1,0. |
| ❌ | `config` | Raw configuration byte. | — | 1090 only, BDS 1,0 data link capability. |
| ❌ | `corrective` | Whether the active RA is corrective (requires a maneuver) vs. preventive. | — | 1090 only, BDS 3,0. |
| ❌ | `cpr_format` | CPR odd/even format flag from the raw compact position report. | — | 1090 only, BDS 0,5/0,6. |
| ❌ | `cpr_lat` | Raw, un-decoded CPR-encoded latitude. | — | 1090 only, BDS 0,5/0,6. |
| ❌ | `cpr_lon` | Raw, un-decoded CPR-encoded longitude. | — | 1090 only, BDS 0,5/0,6. |
| ❌ | `crc_valid` | Whether the message's CRC checksum passed. | — | 1090 only, DF17/18/20/21. |
| ❌ | `cross_link_capability` | Whether the transponder can support DF16 replies. | — | 1090 only, DF0. |
| ❌ | `df` | Downlink Format — the 5-bit code identifying which of ~10 different Mode S/ADS-B message formats a 1090 reply is. | — | 1090 only, always present; no UAT equivalent structurally, though `payload_type` serves a similar use. |
| ❌ | `downlink_elm_throughput` | Downlink Extended Length Message throughput capability. | — | 1090 only, BDS 1,0. |
| ❌ | `downlink_request` | Whether the transponder has more data queued to send. | — | 1090 only, DF4/5/20/21. |
| ❌ | `downward_sense` | Whether the RA commands a downward sense. | — | 1090 only, BDS 3,0. |
| ❌ | `dte_status` | Data Terminal Equipment status field. | — | 1090 only, BDS 1,0. |
| `emergency_state` | `emergency_state` | `Emergency` enum — emergency/priority status. Values: `NO_EMERGENCY`, `GENERAL`, `MEDICAL`, `MINIMUM_FUEL`, `NO_COMMUNICATIONS`, `UNLAWFUL_INTERFERENCE`, `DOWNED_AIRCRAFT`, `RESERVED_7`. | 1, 3 | pyModeS exposes this as a bare `int`. |
| ❌ | `error` | Error message text, part of pyModeS's corrupt-input error envelope for batch/pipe decode modes. | — | 1090 only. |
| `es_in` | ❌ | Capability code — has a 1090ES receiver. | 1, 3 | Packed into pyModeS's `capability_class` bitfield, not individually named there. |
| ❌ | `figure_of_merit` | Confidence/quality indicator for the met report. | — | 1090 only, BDS 4,4. |
| ❌ | `flight_status` | Raw 3-bit flight status code — alert/SPI/on-ground bits. | — | 1090 only, DF4/5/20/21. |
| ❌ | `flight_status_text` | Human-readable decode of `flight_status`. | — | 1090 only, DF4/5/20/21. |
| `geo_minus_baro` | `geo_minus_baro` | Signed delta between geometric and barometric altitude, feet — `geometric - barometric`, derived directly from `altitude`/`altitude_secondary` and their `_type` tags. Derived convenience field, not a new bit read; matches pyModeS's field name. | 1, 2, 5, 6 | `None` if either altitude is unavailable in this frame. |
| `groundspeed` | `groundspeed` | Knots, rounded. Airborne: `√(ns² + ew²)` from the N/S and E/W velocity components. Ground: a direct raw code. | 0–10 | `None` for `RESERVED` airground state. |
| `gva` | ❌ | Geometric Vertical Accuracy, 2-bit raw (0–3) — 95% accuracy bound on GNSS altitude. | 1, 3 | — |
| `heading` | `heading` | Ground-only heading, 1 decimal, from the 11-bit raw track/heading code (`* 360/512`). | 0–10 | Populated instead of `track` only when the ground type code says magnetic or true heading — see `heading_type`. |
| `heading_type` | ❌ | `HeadingType` enum (`MAGNETIC`/`TRUE`) — which kind of heading `heading` is. | 0–10 | No 1090 equivalent — added to preserve the magnetic/true distinction UAT's ground type code carries. `None` whenever `heading` is `None`. |
| ❌ | `hrd` | Horizontal Reference Direction — whether headings are referenced to true or magnetic north. | — | 1090 only, BDS 6,5. |
| ❌ | `humidity` | Relative humidity, %. | — | 1090 only, BDS 4,4. |
| `icao` | `icao` | 24-bit address, 6 hex chars, uppercase. | All | Despite the name, not always a real ICAO address — see `address_qualifier`. |
| ❌ | `icao_verified` | Whether the extracted ICAO address was cross-checked against overlay/parity bits. | — | 1090 only, DF20/21. |
| ❌ | `icing` | Icing intensity code. | — | 1090 only, BDS 4,5. |
| `ident_active` | ❌ | Operational mode bit — the pilot has pressed IDENT. | 1, 3 | Packed into pyModeS's `operational_mode` bitfield, not individually named there. |
| ❌ | `increased_rate` | Whether the RA commands an increased climb/descent rate. | — | 1090 only, BDS 3,0. |
| ❌ | `indicated_airspeed` | Indicated airspeed, knots. | — | 1090 only, BDS 6,0. |
| ❌ | `inertial_vertical_rate` | Inertial (INS/IRS-derived) vertical rate, feet/min. | — | 1090 only, BDS 6,0. |
| ❌ | `issued_ra` | Whether a resolution advisory has been issued. | — | 1090 only, BDS 3,0. |
| `latitude` | `latitude` | Decoded position, 6 decimal places (`raw * 360 / 2^24`). Absolute in every frame — no CPR even/odd pairing needed, unlike 1090. | 0–10 | `None` if there's no valid fix (`nic == 0` and raw lat/lon both `0`). |
| `length` | ❌ | Aircraft length, meters, from the width/length code table. | 0–10 | Ground only. |
| ❌ | `lnav_mode` | Whether LNAV mode is engaged. | — | 1090 only, BDS 6,2. |
| `longitude` | `longitude` | See `latitude`. | 0–10 | Same as `latitude`. |
| ❌ | `mach` | Mach number. | — | 1090 only, BDS 6,0. |
| `magnetic_heading` | `magnetic_heading` | Degrees, 1 decimal — same value as `heading` when `heading_type` is `MAGNETIC`, else `None`. Derived convenience field, not a new bit read; matches pyModeS's field name. | 0–10 | Ground only. |
| ❌ | `microburst` | Microburst intensity code. | — | 1090 only, BDS 4,5. |
| ❌ | `mode_s_specific_services` | Whether Mode S specific services capability is reported. | — | 1090 only, BDS 1,0. |
| ❌ | `mode_s_subnetwork_version` | Which Mode S subnetwork version the transponder implements. | — | 1090 only, BDS 1,0. |
| ❌ | `movement` | Raw groundspeed movement code. | — | 1090 only, BDS 0,6 surface position. |
| ❌ | `multiple_threat` | Whether multiple simultaneous threats are being tracked. | — | 1090 only, BDS 3,0. |
| ❌ | `mv` | Raw ACAS message field, further decoded into BDS 3,0 fields if a TCAS RA is active. | — | 1090 only, DF16. |
| `nac_p` | `nac_p` | Navigation Accuracy Category for Position, 4-bit raw (0–15; only 0–11 defined). Resolves `position_accuracy_epu_m`/`position_accuracy_vepu_m`. | 1, 3 | — |
| `nac_v` | `nac_v` | Navigation Accuracy Category for Velocity, 3-bit raw (0–7; only 0–4 defined). Resolves `velocity_accuracy_hfom_ms`/`velocity_accuracy_vfom_ms`. | 1, 3 | — |
| `nic` | ❌ | Navigation Integrity Category, 4-bit raw (0–15) — confidence in the position fix. Combines with `nic_supplement_a` to resolve `position_containment_radius_m`/`position_vpl_m`. | 0–10 | pyModeS resolves NIC internally from typecode + supplement bits for its own uncertainty functions; the resolved number itself isn't part of its `decode()` output. |
| ❌ | `nic_b` | The single "NIC supplement B" bit carried in the raw airborne position message. | — | 1090 only, BDS 0,5. |
| `nic_baro` | `nic_baro` | Whether the barometric altitude has been cross-checked against another source. | 1, 3 | `bool` here; pyModeS exposes it as a bare `int`. |
| `nic_supplement_a` | `nic_supplement_a` | The one NIC supplement bit UAT has (1090 has two). | 1, 3 | `bool` here; pyModeS exposes it as a bare `int`. |
| ❌ | `no_above` | Whether the RA is a "do not climb above" restriction. | — | 1090 only, BDS 3,0. |
| ❌ | `no_below` | Whether the RA is a "do not descend below" restriction. | — | 1090 only, BDS 3,0. |
| ❌ | `no_left` | Whether the RA is a "do not turn left" restriction (rare horizontal RA variant). | — | 1090 only, BDS 3,0. |
| ❌ | `no_right` | Whether the RA is a "do not turn right" restriction. | — | 1090 only, BDS 3,0. |
| ❌ | `nuc_p` | Navigation Uncertainty Category for Position — the older, pre-NIC/NACp accuracy metric BDS 0,5 also carries for backward compatibility. | — | 1090 only, BDS 0,5. |
| ❌ | `operational_mode` | Raw operational mode bitfield — the packed equivalent of `tcas_ra_active`/`ident_active`/`atc_services`, exposed here as individually named booleans instead. | — | 1090 only, BDS 6,5. |
| ❌ | `overlay_command_capability` | Whether the transponder supports the overlay command capability. | — | 1090 only, BDS 1,0. |
| `payload_type` | ❌ | `PayloadType` enum, 5-bit raw — determines which blocks (State Vector/Mode Status/AUX SV) are present in this frame. Named values: `SHORT`, `LONG`, `SHORT_AUX`, `SHORT_MS`; other raw values (4–31) fall back to the plain int. | All | Serves a similar use to pyModeS's `df` (Downlink Format). |
| `position_accuracy_epu_m` | ❌ | Estimated Position Uncertainty, meters (95%), from `nac_p`. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `position_accuracy_vepu_m` | ❌ | Vertical EPU, meters (95%), from `nac_p`. Only defined for the two highest `nac_p` values. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `position_containment_radius_m` | ❌ | Containment radius implied by `nic` + `nic_supplement_a`. `None` for combinations the spec doesn't define (e.g. `nic=9` is only defined when `nic_supplement_a=True`) — a real gap in the table, not a bug. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `position_offset` | ❌ | Whether the GPS antenna is offset from the nose/wingtip, per the length/width code's convention. | 0–10 | Ground only. |
| `position_vpl_m` | ❌ | Vertical Protection Limit implied by `nic` + `nic_supplement_a`. Same undefined-combination caveat as `position_containment_radius_m`. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| ❌ | `positive` | Whether the RA is a positive (climb/descend) vs. vertical-speed-limit RA. | — | 1090 only, BDS 3,0. |
| ❌ | `ra_terminated` | Whether the RA has been terminated. | — | 1090 only, BDS 3,0. |
| ❌ | `radio_height` | Radio altimeter height, feet. | — | 1090 only, BDS 4,5. |
| ❌ | `raw_msg` | The original raw message hex, included in the error envelope alongside `error`. | — | 1090 only. |
| ❌ | `reply_information` | ACAS/Mode S transponder capability signaled in a short ACAS reply. | — | 1090 only, DF0/16. |
| ❌ | `roll` | Roll angle, degrees. | — | 1090 only, BDS 5,0 track and turn report. |
| `sda` | ❌ | System Design Assurance, 2-bit raw (0–3) — failure-rate classification of the transmitting equipment. | 1, 3 | — |
| ❌ | `selected_altitude` | Selected altitude. | — | 1090 only, BDS 6,2 target state and status report. |
| ❌ | `selected_altitude_fms` | The FMS selected altitude (may differ from the MCP value). | — | 1090 only, BDS 4,0. |
| ❌ | `selected_altitude_mcp` | The MCP/FCU selected altitude. | — | 1090 only, BDS 4,0 selected vertical intention. |
| ❌ | `selected_altitude_source` | Which source the selected altitude came from. | — | 1090 only, BDS 6,2. |
| ❌ | `selected_heading` | Selected heading, degrees. | — | 1090 only, BDS 6,2. |
| ❌ | `sense_reversal` | Whether the RA commands a sense reversal. | — | 1090 only, BDS 3,0. |
| ❌ | `sensitivity_level` | ACAS sensitivity level in use. | — | 1090 only, DF0/16. |
| `sil` | `sil` | Source Integrity Level, 2-bit raw (0–3) — probability the reported position exceeds the NIC containment radius without alerting. | 1, 3 | — |
| `sil_probability_horizontal` | ❌ | Probability `position_containment_radius_m` is exceeded without alerting, from `sil`. Time base given by `sil_supplement`. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `sil_probability_vertical` | ❌ | Probability `position_vpl_m` is exceeded without alerting, from `sil`. Same time-base caveat. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `sil_supplement` | `sil_supplement` | `PER_HOUR` or `PER_SAMPLE` — the time base `sil`'s probabilities apply to, not a different probability table. | 1, 3 | pyModeS exposes this as a bare `int`. |
| `single_antenna` | ❌ | Whether the transmitter uses a single antenna (vs. antenna diversity). | 1, 3 | — |
| `squawk` | `squawk` | Mode 3/A squawk code. A CSID flag in the same raw bits as `callsign` picks whether this field is a callsign or a squawk — UAT has no DF 5/21 equivalent, so this is the *only* source of squawk. | 1, 3 | Mutually exclusive with `callsign`. |
| ❌ | `squitter_capability` | Extended squitter capability flag. | — | 1090 only, BDS 1,0. |
| ❌ | `static_air_temperature` | Static air temperature, °C. | — | 1090 only, BDS 4,4. |
| ❌ | `static_pressure` | Static air pressure, hPa. | — | 1090 only, BDS 4,4. |
| ❌ | `subtype` | 3-bit subtype — airborne vs. surface, GNSS vs. air-referenced groundspeed. | — | 1090 only, BDS 0,9. |
| ❌ | `supported_bds` | Which BDS registers this transponder supports. | — | 1090 only, BDS 1,7 GICB capability report. |
| ❌ | `surveillance_identifier_code` | Surveillance identifier code capability flag. | — | 1090 only, BDS 1,0. |
| ❌ | `surveillance_status` | 2-bit surveillance status field. | — | 1090 only, BDS 0,5. |
| ❌ | `target_altitude_source` | Which source (MCP/FMS/etc.) `selected_altitude_mcp`/`selected_altitude_fms` came from. | — | 1090 only, BDS 4,0. |
| `tcas_operational` | `tcas_operational` | Capability code — TCAS/ACAS is installed and operational. | 1, 3 | Also packed into pyModeS's `capability_class` bitfield. |
| `tcas_ra_active` | ❌ | Operational mode bit — a TCAS/ACAS resolution advisory is currently active. | 1, 3 | 1090's closest concept is the multi-field BDS 3,0 ACAS RA broadcast (`issued_ra`, `corrective`, etc.), not a single boolean. |
| ❌ | `threat_altitude` | The threat aircraft's altitude, when identified by altitude/bearing/range instead. | — | 1090 only, BDS 3,0. |
| ❌ | `threat_bearing` | The threat aircraft's bearing, degrees. | — | 1090 only, BDS 3,0. |
| ❌ | `threat_icao` | The threat aircraft's ICAO address, when `threat_type_indicator` says ICAO-identified. | — | 1090 only, BDS 3,0. |
| ❌ | `threat_range` | The threat aircraft's range, nautical miles. | — | 1090 only, BDS 3,0. |
| ❌ | `threat_type_indicator` | Whether the threat is identified by ICAO address or by altitude/bearing/range. | — | 1090 only, BDS 3,0 ACAS RA broadcast. |
| `tisb_site_id` | ❌ | Ground station site ID. | 0–10 | TIS-B frames only — same 4 raw bits as `utc_coupled`, reinterpreted per `address_qualifier`. |
| `track` | `track` | Track over ground, 1 decimal. Airborne: `atan2` of the N/S and E/W velocity components. Ground: a direct raw code. | 0–10 | Airborne: always this field (never `heading`); ground: only when the type code says "track" rather than heading. |
| ❌ | `track_rate` | Rate of turn, degrees/second. | — | 1090 only, BDS 5,0. |
| ❌ | `track_status` | Track validity bit. | — | 1090 only, BDS 0,6 surface position. |
| `transmit_mso` | ❌ | Message Start Opportunity slot the transmitter used — a radio-layer detail, not aircraft state. | 1, 3 | — |
| ❌ | `transponder_level5` | Whether the transponder is Level 5 (Enhanced Surveillance) capable. | — | 1090 only, BDS 1,0. |
| ❌ | `true_airspeed` | True airspeed, knots. | — | 1090 only, BDS 5,0. |
| ❌ | `true_track` | True track angle, degrees. | — | 1090 only, BDS 5,0. |
| ❌ | `turbulence` | Turbulence intensity code. | — | 1090 only, BDS 4,4. |
| ❌ | `typecode` | ADS-B typecode (bits 33–37 of DF17/18) — which BDS register/subtype a message carries. | — | 1090 only, DF17/18; no UAT equivalent structurally, though `payload_type` serves a similar use. |
| `uat_in` | ❌ | Capability code — has a UAT receiver. | 1, 3 | Packed into pyModeS's `capability_class` bitfield, not individually named there. |
| ❌ | `uplink_elm_throughput` | Uplink Extended Length Message throughput capability. | — | 1090 only, BDS 1,0. |
| `utc_coupled` | ❌ | Whether the frame's time reference is UTC-coupled. | 0–10 | Native ADS-B (non-TIS-B `address_qualifier`) only. |
| ❌ | `utility_message` | IIS/IDS sub-field for interrogator identification. | — | 1090 only, DF4/5/20/21. |
| `velocity_accuracy_hfom_ms` | ❌ | Horizontal Figure of Merit for velocity, m/s, from `nac_v`. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `velocity_accuracy_vfom_ms` | ❌ | Vertical Figure of Merit for velocity, m/s, from `nac_v`. | 1, 3 | Derivable from pyModeS's own `_uncertainty.py`, not auto-called there. |
| `version` | `version` | ADS-B/MOPS version the transmitting equipment implements, 3-bit raw. | 1, 3 | — |
| `vertical_rate` | `vertical_rate` | Feet/min, signed, from the 11-bit raw vertical rate code. | 0–10 | Airborne only — `None` on the ground (those bits hold aircraft dimensions instead). |
| `vertical_status` | `vertical_status` | `"airborne"` or `"on-ground"`, matching pyModeS's exact strings — derived from `airground_state` (both `AIRBORNE_SUBSONIC`/`AIRBORNE_SUPERSONIC` map to `"airborne"`). Derived convenience field, not a new bit read. | 0–10 | `None` for `RESERVED` airground state (no pyModeS equivalent for that state). |
| ❌ | `vnav_mode` | Whether VNAV mode is engaged. | — | 1090 only, BDS 4,0. |
| `vr_source` | `vr_source` | `BARO` or `GNSS` — which kind of altitude `vertical_rate` is derived from. Same values as pyModeS's own `"BARO"`/`"GNSS"` strings, matched exactly. | 0–10 | Airborne only; pyModeS exposes this as a bare `str`. |
| ❌ | `wake_vortex` | Human-readable wake turbulence category text, derived from `category` + typecode. | — | 1090 only, BDS 0,8. |
| `width` | ❌ | Aircraft width, meters, from the width/length code table. | 0–10 | Ground only. |
| ❌ | `wind_direction` | Wind direction, degrees. | — | 1090 only, BDS 4,4. |
| ❌ | `wind_shear` | Wind shear intensity code. | — | 1090 only, BDS 4,5 met hazard report. |
| ❌ | `wind_speed` | Wind speed, knots. | — | 1090 only, BDS 4,4 met routine report. |

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

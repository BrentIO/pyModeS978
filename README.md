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

`payload_type`, `address_qualifier`, `category`, `emergency_state`, `sil_supplement`, `airground_state`,
`altitude_type`, `altitude_secondary_type`, `vr_source`, and `heading_type` are all `IntEnum`s (still
compare/hash equal to their plain-int value). `payload_type`/`address_qualifier`/`category`/`emergency_state`/
`sil_supplement` fall back to the plain int for any raw value with no named member; the other five have every
raw value named, so no fallback applies. `airground_state` does not collapse subsonic/supersonic airborne into
one value -- `AirgroundState.AIRBORNE_SUBSONIC` and `AirgroundState.AIRBORNE_SUPERSONIC` are distinct members,
so collapse them yourself if you don't care about the distinction. `altitude_type`, `altitude_secondary_type`,
and `vr_source` all share the same `AltitudeSource` enum (`BARO`/`GNSS`).

## Data dictionary

Every field either library can return, alphabetical by field name. **pyModeS978 Field** is ours; **pyModeS
Equivalent** is the matching field in pyModeS's 1090 `decode()` output. A ❌ in the pyModeS978 Field column means
that data simply isn't available from a UAT frame; a ❌ in the pyModeS Equivalent column means the reverse --
pyModeS has nothing comparable. pyModeS-only fields are inserted alphabetically as if pyModeS978 had a field of
that same name, so the whole table reads as one merged, alphabetical list rather than "ours first, then
theirs." Where a field's type is one of our `IntEnum`s, its possible values are listed.

Two recurring pyModeS-only patterns, noted once here instead of in every row: pyModeS exposes its Mode
Status-equivalent capability/operational-mode bits as two raw bitfield ints (`capability_class`,
`operational_mode`) rather than breaking them out into named booleans the way
`uat_in`/`es_in`/`tcas_operational`/`tcas_ra_active`/`ident_active`/`atc_services` do; and pyModeS keeps its own
uncertainty lookup tables (`_uncertainty.py`) to itself rather than auto-populating `decode()` output with
them, unlike the `position_accuracy_*`/`velocity_accuracy_*`/`position_containment_*`/`sil_probability_*`
fields here.

| pyModeS978 Field | pyModeS Equivalent | Description | Requirements |
|---|---|---|---|
| ❌ | `acas_hybrid_surveillance` | ACAS hybrid surveillance capability flag. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `acas_operational` | Whether ACAS is operational (the data link capability report's own copy of this flag). | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `acas_resolution_advisory` | Whether ACAS resolution advisory generation is active. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `acas_rtca_version` | Which RTCA ACAS version the equipment implements. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| `address_qualifier` | ❌ | `AddressQualifier` enum — what kind of address `icao` is and where the frame came from. Values: `ADSB_ICAO`, `NATIONAL_RESERVED`, `TISB_ICAO`, `TISB_OTHER`, `VEHICLE`, `FIXED_BEACON`, `RESERVED_6`, `RESERVED_7`. | All payload types (HDR). |
| ❌ | `aircraft_identification_capability` | Whether the transponder can report aircraft identification (BDS 0,8). | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| `airground_state` | ❌ | `AirgroundState` enum — `AIRBORNE_SUBSONIC`, `AIRBORNE_SUPERSONIC`, `ON_GROUND`, or `RESERVED`. Subsonic/supersonic kept distinct, not collapsed into one `AIRBORNE` value. | Payload types 0–10 (State Vector). |
| ❌ | `airspeed` | Air-referenced (not ground) speed, knots — an alternative to `groundspeed` for some subtypes. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,9. |
| ❌ | `airspeed_type` | Whether `airspeed` is true or indicated airspeed. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,9. |
| `altitude` | `altitude` | Feet, from the 12-bit raw altitude code: `(raw - 1) * 25 - 1000`. | Payload types 0–10; `None` if the raw altitude code is `0` (unavailable). |
| ❌ | `altitude_crossing` | Whether the RA commands an altitude crossing maneuver. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `altitude_hold_mode` | Whether altitude hold mode is engaged. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| `altitude_secondary` | ❌ (pyModeS's `geo_minus_baro` is a *delta* between the two altitudes, not a second absolute value -- see `geo_minus_baro` below for the delta itself) | Feet. Whichever altitude type `altitude` *isn't* — if `altitude_type` is `BARO`, this is the GNSS altitude, and vice versa. | Payload types 1, 2, 5, 6 (AUX SV); `None` if the raw AUX SV altitude code is `0`. |
| `altitude_secondary_type` | ❌ | `AltitudeSource` enum (`BARO`/`GNSS`) — always the opposite of `altitude_type`. | Same as `altitude_secondary`. |
| `altitude_type` | ❌ (pyModeS infers baro-vs-GNSS from the raw ADS-B typecode instead of exposing a field) | `AltitudeSource` enum (`BARO`/`GNSS`) — which kind of altitude `altitude` is. | Payload types 0–10; `None` alongside `altitude` when unavailable. |
| ❌ | `approach_mode` | Whether approach mode is engaged. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| `atc_services` | ❌ (`operational_mode` bitfield, see above) | Operational mode bit — aircraft is receiving ATC services. | Payload types 1, 3 (Mode Status). |
| ❌ | `autopilot` | Whether the autopilot is engaged. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,2. |
| ❌ | `baro_pressure_setting` | The pilot's barometric pressure setting, millibars. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| ❌ | `baro_vertical_rate` | Barometric vertical rate, feet/min. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,0. |
| ❌ | `bds` | Which BDS register a message decoded as (e.g. "05", "09"), resolved from `typecode`. | N/A — not decoded by pyModeS978. 1090 only, DF17/18. |
| ❌ | `bds_candidates` | When BDS is ambiguous from typecode alone, the list of registers it might be. | N/A — not decoded by pyModeS978. 1090 only, DF17/18. |
| `callsign` | `callsign` | Flight ID, base-40-decoded from Mode Status's packed character field and whitespace-stripped. | Payload types 1, 3; `None` if this frame's field holds a squawk instead (see `squawk`), or is blank. |
| ❌ | `capability` | 3-bit capability field — transponder's Mode S capability level. | N/A — not decoded by pyModeS978. 1090 only, DF11. |
| ❌ | `capability_class` | Raw capability class bitfield (packs the `uat_in`/`es_in`/`tcas_operational`-equivalent bits together instead of naming them individually). | N/A — not decoded by pyModeS978. 1090 only, BDS 6,5 operational status report. |
| ❌ | `capability_text` | Human-readable decode of `capability`. | N/A — not decoded by pyModeS978. 1090 only, DF11. |
| `category` | `category` (bare `int`; ours is `EmitterCategory`) | Aircraft/vehicle emitter category. Values: `NO_INFORMATION`, `LIGHT`, `MEDIUM`, `MEDIUM_LARGE`, `MEDIUM_LARGE_HIGH_VORTEX`, `HEAVY`, `HIGHLY_MANEUVERABLE`, `ROTORCRAFT`, `RESERVED_8`, `GLIDER_SAILPLANE`, `LIGHTER_THAN_AIR`, `PARACHUTIST_SKYDIVER`, `ULTRALIGHT_HANGGLIDER_PARAGLIDER`, `RESERVED_13`, `UAV`, `SPACE_TRANSATMOSPHERIC`, `RESERVED_16`, `EMERGENCY_VEHICLE`, `SERVICE_VEHICLE`, `POINT_OBSTACLE`, `CLUSTER_OBSTACLE`, `LINE_OBSTACLE`, `RESERVED_22`–`RESERVED_39`. pyModeS never named these values — a deviation from pyModeS predating any parity effort, not a #29 decision. | Payload types 1, 3. |
| ❌ | `common_usage_gicb_capability` | Whether the transponder reports common-usage GICB capability (BDS 1,7). | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `config` | Raw configuration byte. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0 data link capability. |
| ❌ | `corrective` | Whether the active RA is corrective (requires a maneuver) vs. preventive. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `cpr_format` | CPR odd/even format flag from the raw compact position report. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5/0,6. |
| ❌ | `cpr_lat` | Raw, un-decoded CPR-encoded latitude. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5/0,6. |
| ❌ | `cpr_lon` | Raw, un-decoded CPR-encoded longitude. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5/0,6. |
| ❌ | `crc_valid` | Whether the message's CRC checksum passed. | N/A — not decoded by pyModeS978. 1090 only, DF17/18/20/21. |
| ❌ | `cross_link_capability` | Whether the transponder can support DF16 replies. | N/A — not decoded by pyModeS978. 1090 only, DF0. |
| ❌ | `df` | Downlink Format — the 5-bit code identifying which of ~10 different Mode S/ADS-B message formats a 1090 reply is. | N/A — not decoded by pyModeS978. 1090 only, always present; no UAT equivalent structurally, though `payload_type` plays an analogous dispatch role. |
| ❌ | `downlink_elm_throughput` | Downlink Extended Length Message throughput capability. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `downlink_request` | Whether the transponder has more data queued to send. | N/A — not decoded by pyModeS978. 1090 only, DF4/5/20/21. |
| ❌ | `downward_sense` | Whether the RA commands a downward sense. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `dte_status` | Data Terminal Equipment status field. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| `emergency_state` | `emergency_state` (bare `int`; ours is `Emergency`) | `Emergency` enum — emergency/priority status. Values: `NO_EMERGENCY`, `GENERAL`, `MEDICAL`, `MINIMUM_FUEL`, `NO_COMMUNICATIONS`, `UNLAWFUL_INTERFERENCE`, `DOWNED_AIRCRAFT`, `RESERVED_7`. | Payload types 1, 3. |
| ❌ | `error` | Error message text, part of pyModeS's corrupt-input error envelope for batch/pipe decode modes. | N/A — not decoded by pyModeS978. 1090 only. |
| `es_in` | ❌ (`capability_class` bitfield, see above) | Capability code — has a 1090ES receiver. | Payload types 1, 3. |
| ❌ | `figure_of_merit` | Confidence/quality indicator for the met report. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| ❌ | `flight_status` | Raw 3-bit flight status code — alert/SPI/on-ground bits. | N/A — not decoded by pyModeS978. 1090 only, DF4/5/20/21. |
| ❌ | `flight_status_text` | Human-readable decode of `flight_status`. | N/A — not decoded by pyModeS978. 1090 only, DF4/5/20/21. |
| `geo_minus_baro` | `geo_minus_baro` | Signed delta between geometric and barometric altitude, feet -- `geometric - barometric`, derived directly from `altitude`/`altitude_secondary` and their `_type` tags. Derived convenience field, not a new bit read; matches pyModeS's field name. | Payload types 1, 2, 5, 6 (AUX SV); `None` if either altitude is unavailable in this frame. |
| `groundspeed` | `groundspeed` | Knots, rounded. Airborne: `√(ns² + ew²)` from the N/S and E/W velocity components. Ground: a direct raw code. | Payload types 0–10; `None` for `RESERVED` airground state. |
| `gva` | ❌ | Geometric Vertical Accuracy, 2-bit raw (0–3) — 95% accuracy bound on GNSS altitude. | Payload types 1, 3. |
| `heading` | `heading` | Ground-only heading, 1 decimal, from the 11-bit raw track/heading code (`* 360/512`). | Payload types 0–10; populated instead of `track` only when the ground type code says magnetic or true heading — see `heading_type`. |
| `heading_type` | ❌ (no 1090 equivalent — added to preserve the magnetic/true distinction UAT's ground type code carries) | `HeadingType` enum (`MAGNETIC`/`TRUE`) — which kind of heading `heading` is. | Payload types 0–10; `None` whenever `heading` is `None`. |
| ❌ | `hrd` | Horizontal Reference Direction — whether headings are referenced to true or magnetic north. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,5. |
| ❌ | `humidity` | Relative humidity, %. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| `icao` | `icao` | 24-bit address, 6 hex chars, uppercase. | All payload types; despite the name, not always a real ICAO address — see `address_qualifier`. |
| ❌ | `icao_verified` | Whether the extracted ICAO address was cross-checked against overlay/parity bits. | N/A — not decoded by pyModeS978. 1090 only, DF20/21. |
| ❌ | `icing` | Icing intensity code. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,5. |
| `ident_active` | ❌ (`operational_mode` bitfield, see above) | Operational mode bit — the pilot has pressed IDENT. | Payload types 1, 3. |
| ❌ | `increased_rate` | Whether the RA commands an increased climb/descent rate. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `indicated_airspeed` | Indicated airspeed, knots. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,0. |
| ❌ | `inertial_vertical_rate` | Inertial (INS/IRS-derived) vertical rate, feet/min. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,0. |
| ❌ | `issued_ra` | Whether a resolution advisory has been issued. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| `latitude` | `latitude` | Decoded position, 6 decimal places (`raw * 360 / 2^24`). Absolute in every frame — no CPR even/odd pairing needed, unlike 1090. | Payload types 0–10; `None` if there's no valid fix (`nic == 0` and raw lat/lon both `0`). |
| `length` | ❌ | Aircraft length, meters, from the width/length code table. | Payload types 0–10; ground only. |
| ❌ | `lnav_mode` | Whether LNAV mode is engaged. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,2. |
| `longitude` | `longitude` | See `latitude`. | Same as `latitude`. |
| ❌ | `mach` | Mach number. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,0. |
| `magnetic_heading` | `magnetic_heading` | Degrees, 1 decimal — same value as `heading` when `heading_type` is `MAGNETIC`, else `None`. Derived convenience field, not a new bit read; matches pyModeS's field name. | Payload types 0–10; ground only. |
| ❌ | `microburst` | Microburst intensity code. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,5. |
| ❌ | `mode_s_specific_services` | Whether Mode S specific services capability is reported. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `mode_s_subnetwork_version` | Which Mode S subnetwork version the transponder implements. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `movement` | Raw groundspeed movement code. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,6 surface position. |
| ❌ | `multiple_threat` | Whether multiple simultaneous threats are being tracked. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `mv` | Raw ACAS message field, further decoded into BDS 3,0 fields if a TCAS RA is active. | N/A — not decoded by pyModeS978. 1090 only, DF16. |
| `nac_p` | `nac_p` | Navigation Accuracy Category for Position, 4-bit raw (0–15; only 0–11 defined). Resolves `position_accuracy_epu_m`/`position_accuracy_vepu_m`. | Payload types 1, 3. |
| `nac_v` | `nac_v` | Navigation Accuracy Category for Velocity, 3-bit raw (0–7; only 0–4 defined). Resolves `velocity_accuracy_hfom_ms`/`velocity_accuracy_vfom_ms`. | Payload types 1, 3. |
| `nic` | ❌ (pyModeS resolves NIC internally from typecode + supplement bits for its own uncertainty functions, but never exposes the resolved number as a `decode()` output key) | Navigation Integrity Category, 4-bit raw (0–15) — confidence in the position fix. Combines with `nic_supplement_a` to resolve `position_containment_radius_m`/`position_vpl_m`. | Payload types 0–10. |
| ❌ | `nic_b` | The single "NIC supplement B" bit carried in the raw airborne position message. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5. |
| `nic_baro` | `nic_baro` (bare `int`; ours is `bool`) | Whether the barometric altitude has been cross-checked against another source. | Payload types 1, 3. |
| `nic_supplement_a` | `nic_supplement_a` (bare `int`; ours is `bool`; name matches pyModeS exactly — see #29) | The one NIC supplement bit UAT has (1090 has two). | Payload types 1, 3. |
| ❌ | `no_above` | Whether the RA is a "do not climb above" restriction. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `no_below` | Whether the RA is a "do not descend below" restriction. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `no_left` | Whether the RA is a "do not turn left" restriction (rare horizontal RA variant). | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `no_right` | Whether the RA is a "do not turn right" restriction. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `nuc_p` | Navigation Uncertainty Category for Position — the older, pre-NIC/NACp accuracy metric BDS 0,5 also carries for backward compatibility. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5. |
| ❌ | `operational_mode` | Raw operational mode bitfield (packs the `tcas_ra_active`/`ident_active`/`atc_services`-equivalent bits together instead of naming them individually). | N/A — not decoded by pyModeS978. 1090 only, BDS 6,5. |
| ❌ | `overlay_command_capability` | Whether the transponder supports the overlay command capability. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| `payload_type` | ❌ | `PayloadType` enum, 5-bit raw — determines which blocks (State Vector/Mode Status/AUX SV) are present in this frame. Named values: `SHORT`, `LONG`, `SHORT_AUX`, `SHORT_MS`; other raw values (4–31) fall back to the plain int. | All payload types. |
| `position_accuracy_epu_m` | ❌ (see above) | Estimated Position Uncertainty, meters (95%), from `nac_p`. | Payload types 1, 3. |
| `position_accuracy_vepu_m` | ❌ (see above) | Vertical EPU, meters (95%), from `nac_p`. Only defined for the two highest `nac_p` values. | Payload types 1, 3. |
| `position_containment_radius_m` | ❌ (see above) | Containment radius implied by `nic` + `nic_supplement_a`. `None` for combinations the spec doesn't define (e.g. `nic=9` is only defined when `nic_supplement_a=True`) — a real gap in the table, not a bug. | Payload types 1, 3. |
| `position_offset` | ❌ | Whether the GPS antenna is offset from the nose/wingtip, per the length/width code's convention. | Payload types 0–10; ground only. |
| `position_vpl_m` | ❌ (see above) | Vertical Protection Limit implied by `nic` + `nic_supplement_a`. Same undefined-combination caveat as `position_containment_radius_m`. | Payload types 1, 3. |
| ❌ | `positive` | Whether the RA is a positive (climb/descend) vs. vertical-speed-limit RA. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `ra_terminated` | Whether the RA has been terminated. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `radio_height` | Radio altimeter height, feet. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,5. |
| ❌ | `raw_msg` | The original raw message hex, included in the error envelope alongside `error`. | N/A — not decoded by pyModeS978. 1090 only. |
| ❌ | `reply_information` | ACAS/Mode S transponder capability signaled in a short ACAS reply. | N/A — not decoded by pyModeS978. 1090 only, DF0/16. |
| ❌ | `roll` | Roll angle, degrees. | N/A — not decoded by pyModeS978. 1090 only, BDS 5,0 track and turn report. |
| `sda` | ❌ | System Design Assurance, 2-bit raw (0–3) — failure-rate classification of the transmitting equipment. | Payload types 1, 3. |
| ❌ | `selected_altitude` | Selected altitude. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,2 target state and status report. |
| ❌ | `selected_altitude_fms` | The FMS selected altitude (may differ from the MCP value). | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| ❌ | `selected_altitude_mcp` | The MCP/FCU selected altitude. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0 selected vertical intention. |
| ❌ | `selected_altitude_source` | Which source the selected altitude came from. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,2. |
| ❌ | `selected_heading` | Selected heading, degrees. | N/A — not decoded by pyModeS978. 1090 only, BDS 6,2. |
| ❌ | `sense_reversal` | Whether the RA commands a sense reversal. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `sensitivity_level` | ACAS sensitivity level in use. | N/A — not decoded by pyModeS978. 1090 only, DF0/16. |
| `sil` | `sil` | Source Integrity Level, 2-bit raw (0–3) — probability the reported position exceeds the NIC containment radius without alerting. | Payload types 1, 3. |
| `sil_probability_horizontal` | ❌ (see above) | Probability `position_containment_radius_m` is exceeded without alerting, from `sil`. Time base given by `sil_supplement`. | Payload types 1, 3. |
| `sil_probability_vertical` | ❌ (see above) | Probability `position_vpl_m` is exceeded without alerting, from `sil`. Same time-base caveat. | Payload types 1, 3. |
| `sil_supplement` | `sil_supplement` (bare `int`; ours is `SILSupplement`) | `PER_HOUR` or `PER_SAMPLE` — the time base `sil`'s probabilities apply to, not a different probability table. | Payload types 1, 3. |
| `single_antenna` | ❌ | Whether the transmitter uses a single antenna (vs. antenna diversity). | Payload types 1, 3. |
| `squawk` | `squawk` | Mode 3/A squawk code. A CSID flag in the same raw bits as `callsign` picks whether this field is a callsign or a squawk — UAT has no DF 5/21 equivalent, so this is the *only* source of squawk. | Payload types 1, 3; mutually exclusive with `callsign`. |
| ❌ | `squitter_capability` | Extended squitter capability flag. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `static_air_temperature` | Static air temperature, °C. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| ❌ | `static_pressure` | Static air pressure, hPa. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| ❌ | `subtype` | 3-bit subtype — airborne vs. surface, GNSS vs. air-referenced groundspeed. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,9. |
| ❌ | `supported_bds` | Which BDS registers this transponder supports. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,7 GICB capability report. |
| ❌ | `surveillance_identifier_code` | Surveillance identifier code capability flag. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `surveillance_status` | 2-bit surveillance status field. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,5. |
| ❌ | `target_altitude_source` | Which source (MCP/FMS/etc.) `selected_altitude_mcp`/`selected_altitude_fms` came from. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| `tcas_operational` | `tcas_operational` (`capability_class` bitfield in pyModeS, exposed there as its own top-level key too) | Capability code — TCAS/ACAS is installed and operational. | Payload types 1, 3. |
| `tcas_ra_active` | ❌ (1090's closest concept is the multi-field BDS 3,0 ACAS RA broadcast — `issued_ra`, `corrective`, etc. — not a single boolean) | Operational mode bit — a TCAS/ACAS resolution advisory is currently active. | Payload types 1, 3. |
| ❌ | `threat_altitude` | The threat aircraft's altitude, when identified by altitude/bearing/range instead. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `threat_bearing` | The threat aircraft's bearing, degrees. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `threat_icao` | The threat aircraft's ICAO address, when `threat_type_indicator` says ICAO-identified. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `threat_range` | The threat aircraft's range, nautical miles. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0. |
| ❌ | `threat_type_indicator` | Whether the threat is identified by ICAO address or by altitude/bearing/range. | N/A — not decoded by pyModeS978. 1090 only, BDS 3,0 ACAS RA broadcast. |
| `tisb_site_id` | ❌ | Ground station site ID. | Payload types 0–10; TIS-B frames only — same 4 raw bits as `utc_coupled`, reinterpreted per `address_qualifier`. |
| `track` | `track` | Track over ground, 1 decimal. Airborne: `atan2` of the N/S and E/W velocity components. Ground: a direct raw code. | Payload types 0–10; airborne: always this field (never `heading`); ground: only when the type code says "track" rather than heading. |
| ❌ | `track_rate` | Rate of turn, degrees/second. | N/A — not decoded by pyModeS978. 1090 only, BDS 5,0. |
| ❌ | `track_status` | Track validity bit. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,6 surface position. |
| `transmit_mso` | ❌ | Message Start Opportunity slot the transmitter used — a radio-layer detail, not aircraft state. | Payload types 1, 3. |
| ❌ | `transponder_level5` | Whether the transponder is Level 5 (Enhanced Surveillance) capable. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| ❌ | `true_airspeed` | True airspeed, knots. | N/A — not decoded by pyModeS978. 1090 only, BDS 5,0. |
| ❌ | `true_track` | True track angle, degrees. | N/A — not decoded by pyModeS978. 1090 only, BDS 5,0. |
| ❌ | `turbulence` | Turbulence intensity code. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| ❌ | `typecode` | ADS-B typecode (bits 33–37 of DF17/18) — which BDS register/subtype a message carries. | N/A — not decoded by pyModeS978. 1090 only, DF17/18; no UAT equivalent structurally, though `payload_type` plays an analogous dispatch role. |
| `uat_in` | ❌ (`capability_class` bitfield, see above) | Capability code — has a UAT receiver. | Payload types 1, 3. |
| ❌ | `uplink_elm_throughput` | Uplink Extended Length Message throughput capability. | N/A — not decoded by pyModeS978. 1090 only, BDS 1,0. |
| `utc_coupled` | ❌ | Whether the frame's time reference is UTC-coupled. | Payload types 0–10; native ADS-B (non-TIS-B `address_qualifier`) only. |
| ❌ | `utility_message` | IIS/IDS sub-field for interrogator identification. | N/A — not decoded by pyModeS978. 1090 only, DF4/5/20/21. |
| `velocity_accuracy_hfom_ms` | ❌ (see above) | Horizontal Figure of Merit for velocity, m/s, from `nac_v`. | Payload types 1, 3. |
| `velocity_accuracy_vfom_ms` | ❌ (see above) | Vertical Figure of Merit for velocity, m/s, from `nac_v`. | Payload types 1, 3. |
| `version` | `version` | ADS-B/MOPS version the transmitting equipment implements, 3-bit raw. | Payload types 1, 3. |
| `vertical_rate` | `vertical_rate` | Feet/min, signed, from the 11-bit raw vertical rate code. | Payload types 0–10; airborne only — `None` on the ground (those bits hold aircraft dimensions instead). |
| `vertical_status` | `vertical_status` | `"airborne"` or `"on-ground"`, matching pyModeS's exact strings -- derived from `airground_state` (both `AIRBORNE_SUBSONIC`/`AIRBORNE_SUPERSONIC` map to `"airborne"`). Derived convenience field, not a new bit read. | Payload types 0–10; `None` for `RESERVED` airground state (no pyModeS equivalent for that state). |
| ❌ | `vnav_mode` | Whether VNAV mode is engaged. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,0. |
| `vr_source` | `vr_source` (bare `str`; ours is `AltitudeSource`) | `BARO` or `GNSS` — which kind of altitude `vertical_rate` is derived from. Same values as pyModeS's own `"BARO"`/`"GNSS"` strings, matched exactly. | Payload types 0–10; airborne only. |
| ❌ | `wake_vortex` | Human-readable wake turbulence category text, derived from `category` + typecode. | N/A — not decoded by pyModeS978. 1090 only, BDS 0,8. |
| `width` | ❌ | Aircraft width, meters, from the width/length code table. | Payload types 0–10; ground only. |
| ❌ | `wind_direction` | Wind direction, degrees. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4. |
| ❌ | `wind_shear` | Wind shear intensity code. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,5 met hazard report. |
| ❌ | `wind_speed` | Wind speed, knots. | N/A — not decoded by pyModeS978. 1090 only, BDS 4,4 met routine report. |

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

# Tables verified against pyModeS's src/pyModeS/_uncertainty.py (junzis/pyModeS, 1090 side).
# NACp/NACv/SIL are self-contained (no supplement needed) and ported directly.
#
# NIC -> containment radius is the one UAT-specific judgment call: 1090 needs two
# supplement bits (hence pyModeS has both NICv1 and NICv2 tables), but UAT only has
# one (nic_supplement, #22) -- there's no second bit hiding anywhere (confirmed via
# FlightAware's dump978, which marks State Vector's otherwise-unused bit as reserved,
# not a second NIC supplement). So only the single-supplement NICv1 table applies here.

# nac_p -> (EPU meters, VEPU meters)
_NACP = {
    11: (3, 4),
    10: (10, 15),
    9: (30, 45),
    8: (93, None),
    7: (185, None),
    6: (556, None),
    5: (926, None),
    4: (1852, None),
    3: (3704, None),
    2: (7408, None),
    1: (18520, None),
    0: (None, None),
}

# nac_v -> (HFOMr m/s, VFOMr m/s)
_NACV = {
    0: (None, None),
    1: (10, 15.2),
    2: (3, 4.5),
    3: (1, 1.5),
    4: (0.3, 0.46),
}

# sil -> (PE_RCu, PE_VPL) -- dimensionless probabilities; sil_supplement tells you the
# time base (per-flight-hour vs. per-sample) these apply to, not a different table.
_SIL = {
    3: (1e-7, 2e-7),
    2: (1e-5, 1e-5),
    1: (1e-3, 1e-3),
    0: (None, None),
}

# (nic, int(nic_supplement)) -> (Rc meters, VPL meters). Some combinations have no
# entry at all (e.g. nic=9 is only defined for supplement=1) -- faithfully mirrored
# as None, not guessed at.
_NIC_V1 = {
    (11, 0): (7.5, 11),
    (10, 0): (25, 37.5),
    (9, 1): (75, 112),
    (8, 0): (185, None),
    (7, 0): (370, None),
    (6, 0): (926, None),
    (6, 1): (1111, None),
    (5, 0): (1852, None),
    (4, 0): (3702, None),
    (3, 1): (7408, None),
    (2, 0): (14008, None),
    (1, 0): (37000, None),
    (0, 0): (None, None),
}

FIELDS = (
    "position_accuracy_epu_m",
    "position_accuracy_vepu_m",
    "velocity_accuracy_hfom_ms",
    "velocity_accuracy_vfom_ms",
    "position_containment_radius_m",
    "position_vpl_m",
    "sil_probability_horizontal",
    "sil_probability_vertical",
)


def derive(*, nic: int, nic_supplement: bool, nac_p: int, nac_v: int, sil: int) -> dict:
    epu, vepu = _NACP.get(nac_p, (None, None))
    hfom, vfom = _NACV.get(nac_v, (None, None))
    pe_rcu, pe_vpl = _SIL.get(sil, (None, None))
    rc, vpl = _NIC_V1.get((nic, int(nic_supplement)), (None, None))

    return {
        "position_accuracy_epu_m": epu,
        "position_accuracy_vepu_m": vepu,
        "velocity_accuracy_hfom_ms": hfom,
        "velocity_accuracy_vfom_ms": vfom,
        "position_containment_radius_m": rc,
        "position_vpl_m": vpl,
        "sil_probability_horizontal": pe_rcu,
        "sil_probability_vertical": pe_vpl,
    }

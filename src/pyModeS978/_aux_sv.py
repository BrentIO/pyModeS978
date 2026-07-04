from ._bits import read_uint

FIELDS = ("altitude_secondary", "altitude_secondary_type")


def decode(payload: bytes) -> dict:
    raw_alt = read_uint(payload, 232, 12)

    altitude_secondary = altitude_secondary_type = None
    if raw_alt != 0:
        altitude_secondary = (raw_alt - 1) * 25 - 1000
        # Opposite of the primary altitude's type -- same bit State Vector reads for its
        # own altitude_type (bit 79), ternary inverted.
        altitude_secondary_type = "baro" if read_uint(payload, 79, 1) else "geo"

    return {
        "altitude_secondary": altitude_secondary,
        "altitude_secondary_type": altitude_secondary_type,
    }

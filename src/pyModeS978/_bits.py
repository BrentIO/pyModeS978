def read_uint(payload: bytes, start_bit: int, num_bits: int) -> int:
    """Unsigned int from `num_bits` bits starting at `start_bit` (bit 0 = MSB of payload[0])."""
    value = int.from_bytes(payload, "big")
    shift = len(payload) * 8 - start_bit - num_bits
    return (value >> shift) & ((1 << num_bits) - 1)

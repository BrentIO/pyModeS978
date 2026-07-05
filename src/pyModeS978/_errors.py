class DecodeError(ValueError):
    """Base class for all pyModeS978 decode errors."""


class InvalidHexError(DecodeError):
    """Raised when the input (after prefix/metadata stripping) contains non-hex
    characters, or an odd number of hex characters."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"invalid hex input: {raw!r}")
        self.raw = raw


class InvalidLengthError(DecodeError):
    """Raised when the decoded payload isn't 18, 34, or 432 bytes."""

    def __init__(
        self, *, raw: str, actual: int, expected: tuple[int, ...] = (18, 34, 432)
    ) -> None:
        exp = " or ".join(str(e) for e in expected)
        super().__init__(f"expected {exp} bytes, got {actual}")
        self.raw = raw
        self.actual = actual
        self.expected = expected


class DirectionMismatchError(DecodeError):
    """Raised when the dump978-fa direction prefix (-/+) disagrees with the
    direction implied by the actual byte length."""

    def __init__(self, *, raw: str, asserted: str, actual: str) -> None:
        super().__init__(f"prefix asserts {asserted}, but byte length implies {actual}")
        self.raw = raw
        self.asserted = asserted
        self.actual = actual

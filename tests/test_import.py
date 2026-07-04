import pytest

import pyModeS978


def test_decode_not_implemented():
    with pytest.raises(NotImplementedError):
        pyModeS978.decode("00" * 18)

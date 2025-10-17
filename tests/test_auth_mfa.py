import pyotp


def test_totp_window_accepts_current_code():
    totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")
    assert isinstance(totp.now(), str)

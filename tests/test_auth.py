import pytest

from learnus.auth import LoginError, login


def test_login_error_is_exception():
    assert issubclass(LoginError, Exception)


def test_login_raises_on_empty_credentials():
    with pytest.raises(LoginError):
        login("", "")

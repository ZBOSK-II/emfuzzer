import pytest

from coapper.Config import Config


def test_returns_int() -> None:
    conf = Config({"a": 2, "b": 3, "sub": {"x": 42}})

    assert conf.get_int("a") == 2
    assert conf.get_int("b") == 3
    assert conf.get_int("sub", "x") == 42


def test_throws_when_not_int() -> None:
    conf = Config({"a": "2", "b": 3.5, "sub": {"x": 42}})

    with pytest.raises(TypeError):
        conf.get_int("a")
    with pytest.raises(TypeError):
        conf.get_int("b")
    with pytest.raises(TypeError):
        conf.get_int("sub")


def test_returns_float() -> None:
    conf = Config({"a": 2.5, "b": 3, "sub": {"x": 42.4}})

    assert conf.get_float("a") == 2.5
    assert conf.get_float("b") == 3
    assert conf.get_float("sub", "x") == 42.4


def test_throws_when_not_float() -> None:
    conf = Config({"a": "2.5", "b": "3", "sub": {"x": 42.4}})

    with pytest.raises(TypeError):
        conf.get_float("a")
    with pytest.raises(TypeError):
        conf.get_float("b")
    with pytest.raises(TypeError):
        conf.get_float("sub")


def test_returns_str() -> None:
    conf = Config({"a": "x", "b": "y", "sub": {"c": "z"}})

    assert conf.get_str("a") == "x"
    assert conf.get_str("b") == "y"
    assert conf.get_str("sub", "c") == "z"


def test_throws_when_not_str() -> None:
    conf = Config({"a": 2.5, "b": 3, "sub": {"x": "z"}})

    with pytest.raises(TypeError):
        conf.get_str("a")
    with pytest.raises(TypeError):
        conf.get_str("b")
    with pytest.raises(TypeError):
        conf.get_str("sub")

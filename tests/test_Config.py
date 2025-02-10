import pytest

from coapper.Config import Config


def test_throws_on_unknown_key() -> None:
    conf = Config({"a": 1, "b": 2, "c": {"d": 3}})

    with pytest.raises(KeyError):
        conf.get_int("x")
    with pytest.raises(KeyError):
        conf.get_int("c", "x")


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


def test_returns_str_list() -> None:
    conf = Config({"a": ["x", "y", "z"], "sub": {"b": ["1", "2", "3"]}})

    assert conf.get_str_list("a") == ["x", "y", "z"]
    assert conf.get_str_list("sub", "b") == ["1", "2", "3"]


def test_throws_when_not_str_list() -> None:
    conf = Config({"a": 2.5, "b": [3], "sub": {"x": "z"}})

    with pytest.raises(TypeError):
        conf.get_str_list("a")
    with pytest.raises(TypeError):
        conf.get_str_list("b")
    with pytest.raises(TypeError):
        conf.get_str_list("sub")


def test_returns_config_list() -> None:
    conf = Config({"a": [{"x": "y"}, {"z": 2}], "sub": {"b": [{"a": "1"}]}})

    assert [c.to_dict() for c in conf.get_config_list("a")] == [{"x": "y"}, {"z": 2}]
    assert [c.to_dict() for c in conf.get_config_list("sub", "b")] == [{"a": "1"}]


def test_throws_when_not_config_list() -> None:
    conf = Config({"a": 2.5, "b": [3], "sub": {"x": "z"}})

    with pytest.raises(TypeError):
        conf.get_config_list("a")
    with pytest.raises(TypeError):
        conf.get_config_list("b")
    with pytest.raises(TypeError):
        conf.get_config_list("sub")


def test_returns_bool() -> None:
    conf = Config({"a": True, "b": 0, "sub": {"c": 1}})

    assert conf.get_bool("a")
    assert not conf.get_bool("b")
    assert conf.get_bool("sub", "c")


def test_throws_when_not_bool() -> None:
    conf = Config({"a": 2.5, "b": "true", "sub": {"x": "z"}})

    with pytest.raises(TypeError):
        conf.get_bool("a")
    with pytest.raises(TypeError):
        conf.get_bool("b")
    with pytest.raises(TypeError):
        conf.get_bool("sub")

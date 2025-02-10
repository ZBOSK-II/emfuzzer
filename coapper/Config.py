import json
from pathlib import Path
from typing import Any, Self, cast


class Config:

    def __init__(self, obj: dict[str, Any]):
        self._obj = obj

    def section(self, path: str, *subpath: str) -> Self:
        subsection = cast(dict[str, Any], self._obj[path])
        config = self.__class__(subsection)
        if subpath:
            try:
                config.section(*subpath)
            except KeyError:
                raise KeyError(path, *subpath)
        return config

    def _get_value(self, path: str, *subpath: str) -> Any:
        if subpath:
            try:
                return self.section(path)._get_value(*subpath)
            except KeyError:
                raise KeyError(path, *subpath)
        return self._obj[path]

    def get_int(self, path: str, *subpath: str) -> int:
        value = self._get_value(path, *subpath)
        if type(value) is not int:
            raise TypeError("not an int", path, *subpath)
        return value

    def get_float(self, path: str, *subpath: str) -> float:
        value = self._get_value(path, *subpath)
        if type(value) not in (int, float):
            raise TypeError("not an float", path, *subpath)
        return float(value)

    def get_str(self, path: str, *subpath: str) -> str:
        value = self._get_value(path, *subpath)
        if type(value) is not str:
            raise TypeError("not an str", path, *subpath)
        return value

    def get_str_list(self, path: str, *subpath: str) -> list[str]:
        value = self._get_value(path, *subpath)
        if type(value) is not list:
            raise TypeError("not an list", path, *subpath)
        if any(type(x) is not str for x in value):
            raise TypeError("not all elements are str", path, *subpath)
        return value

    def to_dict(self) -> dict[str, Any]:
        return self._obj

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with path.open() as file:
            config = cls(json.load(file))
            config._obj["__path__"] = str(path)
            return config

# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module for loading application configuration.
"""

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
                raise KeyError(path, *subpath) from None
        return config

    def _get_value(self, path: str, *subpath: str) -> Any:
        if subpath:
            try:
                # pylint: disable=protected-access
                return self.section(path)._get_value(*subpath)
            except KeyError:
                raise KeyError(path, *subpath) from None
        return self._obj[path]

    def get_int(self, path: str, *subpath: str) -> int:
        value = self._get_value(path, *subpath)
        if not isinstance(value, int):
            raise TypeError("not an int", path, *subpath)
        return value

    def get_float(self, path: str, *subpath: str) -> float:
        value = self._get_value(path, *subpath)
        if type(value) not in (int, float):
            raise TypeError("not an float", path, *subpath)
        return float(value)

    def get_bool(self, path: str, *subpath: str) -> bool:
        value = self._get_value(path, *subpath)
        if type(value) not in (int, bool):
            raise TypeError("not an bool", path, *subpath)
        return bool(value)

    def get_str(self, path: str, *subpath: str) -> str:
        value = self._get_value(path, *subpath)
        if not isinstance(value, str):
            raise TypeError("not an str", path, *subpath)
        return value

    def get_config_list(self, path: str, *subpath: str) -> list[Self]:
        value = self._get_value(path, *subpath)
        if not isinstance(value, list):
            raise TypeError("not an list", path, *subpath)
        if any(not isinstance(x, dict) for x in value):
            raise TypeError("not all elements are dict", path, *subpath)
        return [self.__class__(v) for v in value]

    def get_str_list(self, path: str, *subpath: str) -> list[str]:
        value = self._get_value(path, *subpath)
        if not isinstance(value, list):
            raise TypeError("not an list", path, *subpath)
        if any(not isinstance(x, str) for x in value):
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

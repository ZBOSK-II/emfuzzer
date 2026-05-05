# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module for loading application configuration.
"""

import json
from pathlib import Path
from typing import Any, Self, Sequence, cast


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
            # pylint: disable=protected-access
            return self.section(path)._get_value(*subpath)
        return self._obj.get(path)

    def _get_required_value(self, path: str, *subpath: str) -> Any:
        value = self._get_value(path, *subpath)
        if value is None:
            raise KeyError(path, *subpath)
        return value

    def _get_value_typed[T: int | float | str | bool](
        self,
        path: str,
        *subpath: str,
        value_type: type[T],
        optional_types: Sequence[type] = (),
        fallback: T | None = None,
    ) -> T:
        value = self._get_value(path, *subpath)
        if value is None:
            if fallback is None:
                raise KeyError(path, *subpath)
            return fallback
        if type(value) not in (value_type, *optional_types):
            raise TypeError(
                f"Expected value type: {value_type.__name__}, found: {type(value).__name__}",
                path,
                *subpath,
            )
        return cast(T, value_type(value))

    def get_int(self, path: str, *subpath: str, fallback: int | None = None) -> int:
        return self._get_value_typed(path, *subpath, value_type=int, fallback=fallback)

    def get_float(
        self, path: str, *subpath: str, fallback: float | None = None
    ) -> float:
        return self._get_value_typed(
            path, *subpath, value_type=float, optional_types=[int], fallback=fallback
        )

    def get_bool(self, path: str, *subpath: str, fallback: bool | None = None) -> bool:
        return self._get_value_typed(
            path, *subpath, value_type=bool, optional_types=[int], fallback=fallback
        )

    def get_str(self, path: str, *subpath: str, fallback: str | None = None) -> str:
        return self._get_value_typed(path, *subpath, value_type=str, fallback=fallback)

    def get_config_list(self, path: str, *subpath: str) -> list[Self]:
        value = self._get_required_value(path, *subpath)
        if not isinstance(value, list):
            raise TypeError("not an list", path, *subpath)
        if any(not isinstance(x, dict) for x in value):
            raise TypeError("not all elements are dict", path, *subpath)
        return [self.__class__(v) for v in value]

    def get_str_list(self, path: str, *subpath: str) -> list[str]:
        value = self._get_required_value(path, *subpath)
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

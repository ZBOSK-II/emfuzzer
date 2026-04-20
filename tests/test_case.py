# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
case module tests.
"""

from pathlib import Path

from emtorch.arguments import Arguments
from emtorch.case.instance import CaseInstance


def _given_data(*args: str) -> Arguments:
    return Arguments(data=[Path(p) for p in args], output_prefix="", config=Path())


def _cases_ids(cases: list[CaseInstance]) -> list[str]:
    return [c.identifier for c in cases]


def _data_ids(cases: list[CaseInstance]) -> list[str]:
    return [c.data.identifier for c in cases]


def test_for_empty_args_builds_empty_list() -> None:
    args = _given_data()

    cases = CaseInstance.list_from(args)

    assert len(cases) == 0


def test_for_single_items_args_builds_simple_list() -> None:
    args = _given_data("a")

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a"]
    assert _data_ids(cases) == ["a"]


def test_for_multiple_items_args_builds_list() -> None:
    args = _given_data("a", "b", "c")

    cases = CaseInstance.list_from(args)

    assert _cases_ids(cases) == ["a", "b", "c"]
    assert _data_ids(cases) == ["a", "b", "c"]

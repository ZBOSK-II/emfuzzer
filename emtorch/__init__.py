# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Main module of the application.
"""

import json
import logging

from .arguments import Arguments
from .case import Case
from .config import Config
from .context import Context
from .results import Results

logger = logging.getLogger(__name__)


def execute(args: Arguments, config: Config) -> Results:
    with Context(config) as context:
        case = Case.from_config(context)

        for path in args.data:
            with context.enter_case(path) as case_context:
                case.execute(case_context)
            case.wait_between_cases()

        return context.results


def run(args: Arguments, config: Config) -> int:
    results = execute(args, config)

    logger.info(f"Results:\n {results.summary()}")

    with open(args.output_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(results.to_dict(), f, indent=2)
        f.write("\n")

    return results.total_errors()

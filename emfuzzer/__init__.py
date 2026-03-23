# Copyright (c) 2025 Warsaw University of Technology
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
from .delay import Delay
from .injector import Injector
from .results import Results

logger = logging.getLogger(__name__)


def execute(args: Arguments, config: Config) -> Results:
    with Context(config) as context:
        results = context.results
        case = Case.from_config(context)

        injector = Injector.from_config(results=results, context=context)

        delay_before_inject = Delay.from_config(
            "delays", "before_inject", config=config
        )

        for path in args.data:
            with context.enter_case(path) as case_context:
                case_name = case_context.key  # XTODO kill
                with case.execute(case_context):
                    delay_before_inject.wait()
                    injector.inject(case_name, case_context.data, case_context)

                case.wait_between_cases()

        return context.results


def run(args: Arguments, config: Config) -> int:
    results = execute(args, config)

    logger.info(f"Results:\n {results.summary()}")

    with open(args.output_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(results.to_dict(), f, indent=2)
        f.write("\n")

    return results.total_errors()

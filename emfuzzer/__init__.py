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


def run(args: Arguments, config: Config) -> int:
    results = Results(config)

    with Context(config) as context:
        case = Case.from_config(context=context, results=results)

        injector = Injector.from_config(results=results, context=context)

        delay_between_cases = Delay.from_config(
            "delays", "between_cases", config=config
        )
        delay_before_inject = Delay.from_config(
            "delays", "before_inject", config=config
        )

        for path in args.data:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warning(f"No data found, skipping {path}")
                continue

            case_name = str(path)
            results.add_key(case_name)

            with case.execute(case_name):
                delay_before_inject.wait()
                injector.inject(case_name, data)

            delay_between_cases.wait()

        results.finish()
    logger.info(f"Results:\n {results.summary()}")

    with open(args.output_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(results.to_dict(), f, indent=2)
        f.write("\n")

    return results.total_errors()

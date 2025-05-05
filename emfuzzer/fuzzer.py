# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import json
import logging

from .arguments import Arguments
from .coapp import Validator
from .config import Config
from .context import Context
from .delay import Delay
from .monitoring import Monitoring
from .net import Address, Loop
from .results import Results
from .subtasks import SubTasks

logger = logging.getLogger(__name__)


# pylint: disable=too-many-locals
def fuzz(args: Arguments, config: Config) -> int:
    target = Address.from_config(config.section("target"))
    validator = Validator(target, config.get_float("coapp", "validator", "timeout"))

    results = Results(config)
    coapp_results = results.register(
        "coapp", Validator.Result, Validator.Result.SUCCESS
    )

    with Context(config) as context:
        setups = SubTasks.from_config(
            "case", "setups", results=results, context=context
        )
        checks = SubTasks.from_config(
            "case", "checks", results=results, context=context
        )
        monitoring = Monitoring.from_config(
            "case",
            "monitoring",
            results=results,
            context=context,
        )

        delay_between_cases = Delay.from_config(
            "case", "delays", "between_cases", config=config
        )
        delay_before_sending = Delay.from_config(
            "case", "delays", "before_sending", config=config
        )

        with Loop(validator) as loop:
            for path in args.data:
                logger.info(f"Opening {path}")
                with path.open("rb") as file:
                    data = file.read()
                if len(data) == 0:
                    logger.warning(f"No data found, skipping {path}")
                    continue

                case_name = str(path)
                results.add_key(case_name)

                setups.execute_for(case_name)

                with monitoring.monitor(case_name):
                    delay_before_sending.wait()
                    loop.send(target, data)

                    coapp_results.collect(case_name, validator.wait_for_result())
                    checks.execute_for(case_name)

                delay_between_cases.wait()

    results.finish(validator.extra_stats())
    logger.info(f"Results:\n {results.summary()}")

    with open(args.output_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(results.to_dict(), f, indent=2)
        f.write("\n")

    return results.total_errors()

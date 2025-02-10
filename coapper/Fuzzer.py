import json
import logging
import time

from .Arguments import Arguments
from .coapp import Validator
from .Config import Config
from .net import Address, Loop
from .Results import Results
from .subtasks import SubTasks

logger = logging.getLogger(__name__)


def fuzz(args: Arguments, config: Config) -> int:
    target = Address.from_config(config.section("target"))
    validator = Validator(target, config.get_float("coapp", "validator", "timeout"))

    results = Results(config)
    coapp_results = results.register(
        "coapp", Validator.Result, Validator.Result.SUCCESS
    )

    setups = SubTasks.from_config("case", "setups", results=results, config=config)
    checks = SubTasks.from_config("case", "checks", results=results, config=config)

    with Loop(validator) as loop:
        for path in args.data:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warn(f"No data found, skipping {path}")
                continue

            case_name = str(path)
            results.add_key(case_name)

            setups.execute_for(case_name)

            loop.send(target, data)

            coapp_results.collect(case_name, validator.wait_for_result())
            checks.execute_for(case_name)

            time.sleep(config.get_float("case", "delay"))

    results.finish(validator.extra_stats())
    logger.info("Results:\n" + results.summary())

    with open(args.output_prefix + ".json", "w", encoding="utf-8") as f:
        json.dump(results.to_dict(), f, indent=2)
        f.write("\n")

    return results.total_errors()

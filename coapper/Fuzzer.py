import logging
import time
from pathlib import Path

from .coapp import Validator
from .net import Loop
from .ping import Pinger
from .Results import Results

logger = logging.getLogger(__name__)


def fuzz(target: str, files: list[Path], timeout: int, delay: int) -> int:
    validator = Validator(target)
    pinger = Pinger(host=target[0], count=5)  # TODO ping configurable?

    results = Results()
    coapp_results = results.register(
        "coapp", Validator.Result, Validator.Result.SUCCESS
    )
    pinger_results = results.register("pinger", Pinger.Result, Pinger.Result.ALIVE)

    with Loop(validator) as loop:
        for path in files:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warn(f"No data found, skipping {path}")
                continue

            validator.mark_sent()
            loop.send(target, data)

            coapp_results.collect(str(path), validator.wait_for_validation(timeout))
            pinger_results.collect(str(path), pinger.check_alive(timeout))

            time.sleep(delay)

    logger.info("Results:\n" + results.summary())

    return results.total_errors()

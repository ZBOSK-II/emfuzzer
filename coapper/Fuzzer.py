import logging
import time

from .Arguments import Arguments
from .coapp import Validator
from .net import Loop
from .ping import Pinger
from .Results import Results
from .Version import VERSION

logger = logging.getLogger(__name__)


def fuzz(args: Arguments) -> int:
    logger.info(f"Started instance ({VERSION})")
    validator = Validator(args.target)
    pinger = Pinger(host=args.target.host, count=5)  # TODO ping configurable?

    results = Results()
    coapp_results = results.register(
        "coapp", Validator.Result, Validator.Result.SUCCESS
    )
    pinger_results = results.register("pinger", Pinger.Result, Pinger.Result.ALIVE)

    with Loop(validator) as loop:
        for path in args.data:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warn(f"No data found, skipping {path}")
                continue

            key = str(path)
            results.add_key(key)

            loop.send(args.target, data)

            coapp_results.collect(key, validator.wait_for_result(args.timeout))
            pinger_results.collect(key, pinger.check_alive(args.timeout))

            time.sleep(args.delay)

    results.mark_finish()
    logger.info("Results:\n" + results.summary())

    return results.total_errors()

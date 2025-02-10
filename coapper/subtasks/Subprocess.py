import logging
import subprocess
from typing import Self

from ..Config import Config
from . import SubTask

logger = logging.getLogger(__name__)


class Subprocess(SubTask):
    def __init__(
        self,
        args: list[str],
        timeout: float,
        shell: bool = False,
        name: str = "subprocess",
    ):
        super().__init__(name)

        self.args = args
        self.timeout = timeout
        self.shell = shell

    def run(self) -> SubTask.Result:
        logger.info(f"<{self.name()}>: Calling `{' '.join(self.args)}`")
        try:
            result = subprocess.run(
                self.args,
                timeout=self.timeout,
                shell=self.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warn(f"<{self.name()}: Operation timedout")
            return self.Result.TIMEOUT
        except Exception as ex:
            logger.error(f"<{self.name()}>: Operation error", ex)
            return self.Result.ERROR

        if result.returncode != 0:
            logger.warn(f"<{self.name()}>: Operation returned {result.returncode}")
            logger.warn(result.stdout)
            return self.Result.FAILURE

        logger.info(f"<{self.name()}>: Operation finished successfully")
        return self.Result.SUCCESS

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            args=config.get_str_list("cmd"),
            timeout=config.get_float("timeout"),
            shell=config.get_bool("shell"),
        )

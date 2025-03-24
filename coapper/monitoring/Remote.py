import logging
import signal
from typing import Self

from ..Config import Config
from ..ssh import ConnectionConfig, Invoker
from . import Monitor

logger = logging.getLogger(__name__)


class Remote(Monitor):
    def __init__(
        self,
        name: str,
        command: str,
        connection_config: ConnectionConfig,
        timeout: float,
    ):
        super().__init__(name)
        self.invoker = Invoker(
            name=name, command=command, connection_config=connection_config
        )
        self.timeout = timeout

    def start(self) -> bool:
        try:
            self.invoker.open()
            return self.invoker.running
        except Exception as ex:
            logging.error(f"Failed to start monitoring <{self.name()}>: {ex}")
            return False

    def finish(self) -> Monitor.Result:
        try:
            self.invoker.signal(signal.SIGINT)
            result = self.invoker.wait_for_exit(self.timeout)
            self.invoker.close()
            return self.Result.SUCCESS if (result == 0) else self.Result.FAILURE
        except TimeoutError:
            return self.Result.TIMEOUT
        except Exception as ex:
            logging.error(f"Failed to finish monitoring <{self.name()}>: {ex}")
            return self.Result.ERROR

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            command=config.get_str("command"),
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            timeout=config.get_float("timeout"),
        )

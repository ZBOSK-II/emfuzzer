# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
SSH command invoker.
"""

import logging
import signal
import time
from typing import Optional

import paramiko

from .connectionconfig import ConnectionConfig
from .reader import ParamikoStream, Reader

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Invoker:
    def __init__(
        self,
        name: str,
        command: str,
        connection_config: ConnectionConfig,
        start_key: str,
    ):
        self.command = command
        self.connection_config = connection_config

        self.running = False

        self.name = f"<{name}>"

        self.__streams: Optional[
            tuple[ParamikoStream, ParamikoStream, ParamikoStream]
        ] = None

        self.__handle: Optional[paramiko.SSHClient] = None
        self.__pid = 0

        # deferred calls to delay stream retrieving
        self.reader = Reader(self.name, start_key, self.__stdout, self.__stderr)

    def __stdout(self) -> ParamikoStream:
        assert self.__streams is not None
        return self.__streams[1]

    def __stderr(self) -> ParamikoStream:
        assert self.__streams is not None
        return self.__streams[2]

    def open(self) -> None:
        if self.running:
            logger.warning(f"{self.name}: already running")
            return

        logger.info(f"{self.name}: open")
        self.__open_ssh()
        logger.info(f"{self.name}: backend started")
        self.reader.start()
        logger.info(f"{self.name}: reader started")

        self.running = True

    def close(self) -> None:
        logger.info(f"{self.name}: close")
        self.__close_ssh()
        logger.info(f"{self.name}: backend closed")
        self.reader.stop()
        logger.info(f"{self.name}: reader stopped")
        self.running = False

    def wait_for_start(self, timeout: float) -> bool:
        return self.running and self.reader.started_event.wait(timeout)

    def wait_for_exit(self, timeout: float) -> int:
        assert self.__handle is not None

        # NOTE: paramiko ignores timeouts set with channel.settimeout() when waiting for exit
        t0 = time.time()
        time_elapsed = 0.0
        while time_elapsed < timeout:
            if self.__stdout().channel.exit_status_ready():
                self.running = False
                return self.__stdout().channel.recv_exit_status()

            time.sleep(0.05)
            time_elapsed = time.time() - t0

        self.close()
        logger.warning(f"{self.name}: timeout")
        raise TimeoutError(f"Timeout, {self.__pid}")

    def signal(self, sig: signal.Signals) -> None:
        assert self.__handle is not None
        logger.info(f"{self.name}: Sending signal {sig.name} to {self.__pid}")
        inp, _, _ = self.__handle.exec_command(f"kill -{sig.name} {self.__pid}")
        inp.channel.recv_exit_status()

    def __open_ssh(self) -> None:
        try:
            self.__handle = paramiko.SSHClient()
            self.__handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__handle.connect(
                self.connection_config.host,
                self.connection_config.port,
                self.connection_config.username,
                self.connection_config.password,
            )
        except Exception:
            if self.__handle is not None and self.__handle.get_transport() is not None:
                self.__handle.close()
                self.__handle = None
            raise

        command = f"echo $$; exec {self.command}"
        logger.info(f"{self.name} executing via SSH: {command}")
        # get_pty - enables "live" stdout
        self.__streams = self.__handle.exec_command(command, get_pty=True)
        self.__pid = int(self.__stdout().readline())
        logger.info(f"{self.name} started via SSH: {self.__pid}")

    def __close_ssh(self) -> None:
        if self.__handle:
            if self.running:
                kill_command = f"kill {self.__pid}"
                logger.info(f"{self.name}: Killing remotely: '{kill_command}'")
                _, stdout, _ = self.__handle.exec_command(kill_command)
                while not stdout.channel.exit_status_ready():
                    # Loop until command executes
                    pass
                logger.info(f"{self.name}: Kill done")

            self.__handle.close()
            self.__handle = None

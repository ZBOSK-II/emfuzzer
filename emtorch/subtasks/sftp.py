# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing SFTP operation as sub-tasks.
"""

import logging
from abc import abstractmethod
from threading import Thread
from typing import Callable, Self

import paramiko

from ..config import Config
from ..context import CaseContext
from ..context.template import Template
from ..ssh import ConnectionConfig
from ..ssh.client import open_ssh
from .subtask import BasicSubTask

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class SftpTask(BasicSubTask):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        connection_config: ConnectionConfig,
        local_path: str,
        remote_path: str,
        timeout: float,
    ):
        super().__init__(name)
        self.connection_config = connection_config
        self.local_path = Template(local_path)
        self.remote_path = Template(remote_path)
        self.timeout = timeout
        self._ssh: None | paramiko.SSHClient = None
        self._sftp: None | paramiko.SFTPClient = None
        self._thread: None | Thread
        self._finished = False

    def basic_start(self, context: CaseContext) -> bool:
        if not self.__open_ssh():
            return False

        def action() -> None:
            try:
                self.perform_action(
                    self.local_path.evaluate(context),
                    self.remote_path.evaluate(context),
                )
                self._finished = True
            except Exception as ex:  # pylint: disable=broad-exception-caught
                logger.error(f"Failed to complete SFT transfer <{self.name()}>: {ex}")

        self._thread = Thread(target=action)
        self._thread.start()
        return True

    def __open_ssh(self) -> bool:
        try:
            self._ssh = open_ssh(self.connection_config)
            self._sftp = self._ssh.open_sftp()
            return True
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to open SSH connection <{self.name()}>: {ex}")
            if self._sftp is not None:
                self._sftp.close()
                if self._ssh is not None:
                    self._ssh.close()
                self._sftp = None
                self._ssh = None
            return False

    @abstractmethod
    def perform_action(self, local_path: str, remote_path: str) -> None:
        pass

    def finish(self) -> BasicSubTask.Result:
        assert self._sftp
        assert self._ssh
        assert self._thread

        self._thread.join(self.timeout)

        timed_out = self._thread.is_alive()

        self._sftp.close()
        self._ssh.close()

        self._thread.join()

        if self._finished:
            return self.Result.SUCCESS
        if timed_out:
            logger.error(f"SFTP transfer timed-out <{self.name()}>")
            return self.Result.TIMEOUT
        return self.Result.ERROR

    def create_callback(self, infix: str) -> Callable[[int, int], None]:
        def callback(current: int, total: int) -> None:
            logger.info(
                f"{self.local_path} {infix} {self.remote_path}: {current} of {total} bytes"
            )

        return callback


class SftpUpload(SftpTask):
    def perform_action(self, local_path: str, remote_path: str) -> None:
        assert self._sftp
        logger.info(f"SFTP PUT {local_path} -> {remote_path}")
        self._sftp.put(
            localpath=local_path,
            remotepath=remote_path,
            callback=self.create_callback("->"),
        )

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            remote_path=config.get_str("remote_path"),
            local_path=config.get_str("local_path"),
            timeout=config.get_float("timeout"),
        )


class SftpDownload(SftpTask):
    def perform_action(self, local_path: str, remote_path: str) -> None:
        assert self._sftp
        logger.info(f"SFTP GET {local_path} <- {remote_path}")
        self._sftp.get(
            localpath=local_path,
            remotepath=remote_path,
            callback=self.create_callback("<-"),
        )

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            remote_path=config.get_str("remote_path"),
            local_path=config.get_str("local_path"),
            timeout=config.get_float("timeout"),
        )

import logging
import os
import queue
import select
import socket
import threading
import time
from binascii import hexlify

logger = logging.getLogger(__name__)


class Loop:
    def __init__(self, validator):
        self.interrupted = threading.Event()
        self.pipe = os.pipe()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thread = threading.Thread(target=self.__loop, name="NetworkLoop")
        self.queue = queue.Queue()
        self.validator = validator

    def __loop(self):
        while not self.interrupted.is_set():
            rlist, wlist, xlist = select.select(
                self.__build_rlist(), self.__build_wlist(), self.__build_xlist()
            )
            if self.interrupted.is_set():
                break

            self.__process_rlist(rlist)
            self.__process_wlist(wlist)
            self.__process_xlist(xlist)

    def __build_rlist(self):
        return [self.udp, self.pipe[0]]

    def __build_wlist(self):
        if self.queue.empty():
            return []
        return [self.udp]

    def __build_xlist(self):
        return self.__build_rlist() + self.__build_wlist()

    def __process_rlist(self, rlist):
        for fd in rlist:
            if fd == self.udp:
                data, addr = self.udp.recvfrom(1024)  # TODO
                logger.info(f"Received {len(data)} bytes from {addr}: {hexlify(data)}")
                if self.validator:
                    self.validator(addr, data)
            elif fd == self.pipe[0]:
                os.read(self.pipe[0], 1)

    def __process_wlist(self, wlist):
        for fd in wlist:
            try:
                addr, data = self.queue.get_nowait()
            except queue.Empty:
                continue
            logger.info(f"Sending {len(data)} bytes to {addr}: {hexlify(data)}")
            fd.sendto(data, addr)

    def __process_xlist(self, xlist):
        for fd in xlist:
            logger.error(f"Error state on {fd}")
        # TODO anything else?

    def start(self):
        logger.info("Starting network thread")
        self.thread.start()

    def stop(self):
        logger.info("Interrupting network thread")
        self.interrupted.set()
        self.__wake_select()
        self.thread.join()
        self.udp.close()
        logger.info("Network thread stopped")

    def send(self, addr, data):
        self.queue.put((addr, data))
        self.__wake_select()

    def __wake_select(self):
        os.write(self.pipe[1], b"x")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

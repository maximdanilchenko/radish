import logging
import asyncio

from radish.protocol import Error, process_reader, process_writer
from radish.exceptions import RadishBadRequest, RadishConnectionError

from .storage import RadishStore


class Handler:

    __slots__ = (
        "server",
        "reader",
        "writer",
        "closing_delay",
        "_active",
        "_wait_closed",
        "address",
    )

    def __init__(
        self,
        server: "Server",
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        closing_delay: int = None,
    ):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.closing_delay = closing_delay
        self._active = None
        self._wait_closed = None
        self.address = self.writer.get_extra_info("peername")

    async def run(self):
        self._active = True
        while self._active:
            try:
                self._wait_inactive()
                request = await process_reader(self.reader)
                self._cancel_inactive()
                logging.debug(f"Got request from {self.address}: {request}")
                if not isinstance(request, list):
                    raise RadishBadRequest("Bad request format")
                answer = self.server.storage.process_command(*request)
            except RadishBadRequest as e:
                answer = Error(e.msg)
            except (RadishConnectionError, ConnectionError):
                self.close_connection()
                break
            logging.debug(f"Sent response to {self.address}: {answer}")
            await process_writer(self.writer, answer)

    def _wait_inactive(self):
        if self.closing_delay and self._wait_closed is None:
            self._wait_closed = self.server.loop.call_later(
                self.closing_delay, self.close_connection
            )

    def _cancel_inactive(self):
        if self._wait_closed:
            self._wait_closed.cancel()
            self._wait_closed = None

    def close_connection(self):
        if self._active:
            self.writer.close()
            logging.debug(f"Connection from  {self.address} CLOSED")
            self._active = False


class Server:

    __slots__ = (
        "host",
        "port",
        "storage",
        "closing_delay",
        "loop",
        "active_connections",
    )

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7272,
        storage: RadishStore = None,
        loop=None,
        closing_delay=None,
    ):
        self.host = host
        self.port = port
        self.storage = storage or RadishStore()
        self.closing_delay = closing_delay
        self.loop: asyncio.BaseEventLoop = loop or asyncio.get_event_loop()
        self.active_connections = 0

    async def _start_new_handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        handler = Handler(
            self, reader=reader, writer=writer, closing_delay=self.closing_delay
        )

        self.active_connections += 1
        logging.info(
            f'New connection: {writer.get_extra_info("peername")}'
            f" | Total: {self.active_connections} connections"
        )

        await handler.run()

        self.active_connections -= 1
        logging.info(
            f'Connection finished: {writer.get_extra_info("peername")}'
            f" | Total: {self.active_connections} connections"
        )

    def run(self):
        coro = asyncio.start_server(
            self._start_new_handler, self.host, self.port, loop=self.loop
        )
        server = self.loop.run_until_complete(coro)

        host, port = server.sockets[0].getsockname()
        address = f"Serving RadishDB on {host}:{port}"
        print(f"\n{address:_^44}")
        print(
            "\n".join(
                [
                    " _  ___  _ ___   ___  ___  ___  _  ___  _ _ ",
                    "| ||_ _||// __> | . \| . || . \| |/ __>| | |",
                    "| | | |   \__ \ |   /|   || | || |\__ \|   |",
                    "|_| |_|   <___/ |_\_\|_|_||___/|_|<___/|_|_|",
                    "",
                ]
            )
        )

        try:
            self.loop.run_forever()
        finally:
            server.close()
            self.loop.run_until_complete(server.wait_closed())
            self.loop.close()

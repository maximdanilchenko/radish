import logging
import asyncio
from collections import namedtuple

from radish.protocol import process_reader, process_writer
from radish.exceptions import RadishClientError, RadishConnectionError

from .commands import CommandsMixin


Stream = namedtuple("Stream", ["reader", "writer"])


class ConnectionPool:

    __slots__ = ("_loop", "_queue", "_clients", "_inited", "_closed", "_min_size")

    def __init__(
        self,
        host="127.0.0.1",
        port=7272,
        min_size=10,
        max_size=10,
        inactive_time=300,
        loop=None,
    ):
        """
        Radish connection pool holder.

        Usage:

        .. code-block:: python

            pool = await ConnectionPool(**POOL_SETTINGS)
            con = await pool.acquire()
            assert await con.ping() == b'PONG'
            await pool.close()

        Using "async with" statement:

        .. code-block:: python

            async with ConnectionPool(host='127.0.0.1', port=7272) as pool:
                async with pool.acquire() as con:  # type: Connection
                    assert await con.ping() == b'PONG'

        :param host:
            Radish DB server host to connect.

        :param port:
            Radish DB server port to connect.

        :param min_size:
            Number of connection the pool will be initialized with.

        :param max_size:
            Maximum number of connections in the pool.

        :param inactive_time:
            After this number of seconds inactive connections should be closed.

        :param loop:
            Asyncio event loop.
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._queue = asyncio.LifoQueue(maxsize=max_size, loop=self._loop)
        self._clients = []
        for _ in range(max_size):
            cl = Connection(
                host=host, port=port, pool=self, inactive_time=inactive_time
            )
            self._queue.put_nowait(cl)
            cl._acquired = False
            self._clients.append(cl)

        self._inited = False
        self._closed = False
        self._min_size = min_size

    async def _init(self):
        if self._inited:
            return None
        if self._closed:
            raise RadishClientError("Pool is closed")
        connect_tasks = [cl.connect() for cl in self._clients[-self._min_size :]]
        await asyncio.gather(*connect_tasks, loop=self._loop)
        self._inited = True
        return self

    def acquire(self):
        return PoolObjContext(self)

    async def _acquire(self):
        self._check_inited()
        cl = await self._queue.get()
        cl._acquired = True
        logging.debug(f"{cl} popped")
        return cl

    def release(self, entity):
        self._check_inited()
        self._queue.put_nowait(entity)
        entity._acquired = False
        logging.debug(f"{entity} released")

    async def close(self):
        logging.debug(f"Start closing {self}..")
        self._check_inited()
        coros = [cl.close() for cl in self._clients]
        await asyncio.gather(*coros, loop=self._loop)
        self._closed = True
        logging.debug(f"Done closing {self}")

    def _check_inited(self):
        if not self._inited:
            raise RadishClientError("Pool is not inited")
        if self._closed:
            raise RadishClientError("Pool is closed")

    async def __aenter__(self):
        await self._init()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    def __await__(self):
        return self._init().__await__()

    def __repr__(self):
        return f"<Pool {id(self)}>"


class PoolObjContext:

    __slots__ = "pool", "pool_obj"

    def __init__(self, pool):
        self.pool = pool
        self.pool_obj = None

    async def __aenter__(self):
        self.pool_obj = await self.pool._acquire()
        return self.pool_obj

    async def __aexit__(self, *exc):
        await self.pool_obj.close()

    def __await__(self):
        return self.pool._acquire().__await__()


class Connection(CommandsMixin):

    __slots__ = (
        "host",
        "port",
        "_stream",
        "_pool",
        "_connected",
        "_waiting",
        "_inactive_time",
        "_loop",
        "_acquired",
        "try_reconnect",
    )

    def __init__(
        self,
        host="127.0.0.1",
        port=7272,
        *,
        pool=None,
        inactive_time=300,
        loop=None,
        try_reconnect=True,
    ):
        """
        Radish connection holder.

        Usage:

        .. code-block:: python

            con = Connection(host='127.0.0.1', port=7272)
            await con.connect()
            assert await con.set('my_key', 'my_val') == 1
            await con.close()

        Using "async with" statement:

        .. code-block:: python

            async with Connection(host='127.0.0.1', port=7272) as con:
                assert await con.mset(k1=1, k2=b'2', k3='3') == b'OK'

        :param host:
            Radish DB server host to connect.

        :param port:
            Radish DB server port to connect.

        :param pool:
            Pool to hold this connection.

         :param inactive_time:
            After this number of seconds inactive connection should be closed.

        :param loop:
            Asyncio event loop.
        """
        self.host = host
        self.port = port
        self._stream = None
        self._pool = pool
        self._connected = False
        self._waiting = None
        self._inactive_time = inactive_time
        self._loop: asyncio.BaseEventLoop = (
            self._pool._loop if self._pool else loop or asyncio.get_event_loop()
        )
        self._acquired = None
        self.try_reconnect = try_reconnect

    async def connect(self):
        self._cancel_inactive()
        self._stream = Stream(
            *await asyncio.open_connection(self.host, self.port, loop=self._loop)
        )
        self._connected = True
        self._wait_inactive()
        logging.debug(f"{self} connected")

    async def _cancel_task(self):
        if self._inactive_time:
            await asyncio.sleep(self._inactive_time)
            await self.close()

    def _wait_inactive(self):
        if self._waiting is None or self._waiting.cancelled() or self._waiting.done():
            self._waiting = asyncio.ensure_future(self._cancel_task())

    def _cancel_inactive(self):
        if (
            self._waiting is not None
            and not self._waiting.done()
            and not self._waiting.cancelled()
        ):
            self._waiting.cancel()

    async def close(self):
        self._cancel_inactive()
        logging.debug(f"{self} start closing")
        if self._connected:
            await self.execute(b"QUIT")
            # We should release connection from here because we have
            # case of usage from pool without "async with" statement
            if self._pool and self._acquired:
                self._pool.release(self)
            self._stream = None
            self._connected = False
        if self._waiting is not None:
            try:
                await self._waiting
            except asyncio.CancelledError:
                pass
        logging.debug(f"{self} closed")

    async def execute(self, *args):
        self._cancel_inactive()
        if not self._connected:
            await self.connect()
        try:
            await process_writer(self._stream.writer, args)
            if args[0] == b"QUIT":
                resp = None
                self._stream.writer.close()
            else:
                resp = await process_reader(self._stream.reader)
                self._wait_inactive()
        except RadishConnectionError as e:
            logging.error("Connection Error: %s", e.msg)
            if self._pool:
                await self._pool.close()
            raise RadishClientError(e.msg)
        except ConnectionError as e:
            if self.try_reconnect:
                self._connected = False
                return await self.execute(*args)
            if self._pool:
                await self._pool.close()
            raise e
        else:
            return resp

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    def __repr__(self):
        return f'<Connection {id(self)} {self._pool if self._pool else ""}>'

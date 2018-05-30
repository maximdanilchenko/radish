import logging
import asyncio
from collections import namedtuple

from radish.protocol import process_reader, process_writer
from radish.exceptions import RadishClientError, RadishConnectionError

from .flayer import FLayer


Stream = namedtuple('Stream', ['reader', 'writer'])


class ConnectionPool:
    def __init__(self, host='127.0.0.1', port=7272, size=10, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._queue = asyncio.LifoQueue(maxsize=size, loop=self._loop)
        self._clients = []
        for _ in range(size):
            cl = Connection(host=host, port=port, pool=self)
            self._queue.put_nowait(cl)
            self._clients.append(cl)

        self._inited = False
        self._closed = False

    async def _init(self):
        if self._inited:
            return None
        if self._closed:
            raise RadishClientError(b'Pool is closed')
        connect_tasks = [cl.connect() for cl in self._clients]
        await asyncio.gather(*connect_tasks, loop=self._loop)
        self._inited = True

    def acquire(self):
        return PoolObjContext(self)

    async def _acquire(self):
        self._check_inited()
        cl = await self._queue.get()
        logging.debug('popped')
        return cl

    def release(self, entity):
        self._check_inited()
        self._queue.put_nowait(entity)
        logging.debug('released')

    async def close(self):
        self._check_inited()
        self._closed = True
        coros = [cl.close() for cl in self._clients]
        await asyncio.gather(*coros, loop=self._loop)

    def _check_inited(self):
        if not self._inited:
            raise RadishClientError(b'Pool is not inited')
        if self._closed:
            raise RadishClientError(b'Pool is closed')

    async def __aenter__(self):
        await self._init()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    def __await__(self):
        return self._init().__await__()


class PoolObjContext:
    def __init__(self, pool):
        self.pool = pool
        self.pool_obj = None

    async def __aenter__(self):
        self.pool_obj = await self.pool._acquire()
        return self.pool_obj

    async def __aexit__(self, *exc):
        self.pool.release(self.pool_obj)

    def __await__(self):
        return self.pool._acquire().__await__()


class Connection(FLayer):
    def __init__(self, host, port, pool=None):
        self._host = host
        self._port = port
        self._stream = None
        self._pool = pool
        self._in_use = False

    async def connect(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._stream = Stream(*await asyncio.open_connection(self._host,
                                                             self._port,
                                                             loop=loop))
        self._in_use = True

    async def close(self):
        await self.execute(b'QUIT')
        self._stream.writer.close()
        self._stream = None
        self._in_use = False

    async def _execute(self, *args):
        try:
            await process_writer(self._stream.writer, args)
            if args[0] != b'QUIT':
                resp = await process_reader(self._stream.reader)
            else:
                resp = None
        except RadishConnectionError as e:
            logging.error('Connection Error: %s', e.msg)
            if self._pool:
                await self._pool.close()
            raise RadishClientError(e.msg)
        else:
            return resp

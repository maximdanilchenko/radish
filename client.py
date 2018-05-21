from typing import List
import asyncio
from collections import namedtuple

from protocol import process_request, process_response, RadishConnectionError, RadishError


Stream = namedtuple('Stream', ['reader', 'writer'])


class RadishClientError(RadishError):
    """ Client Error """


class Pool:
    def __init__(self, host='127.0.0.1', port=7272, size=10, echo_time=30, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._queue = asyncio.LifoQueue(maxsize=size, loop=self._loop)
        self._clients = []
        for _ in range(size):
            cl = Client(host=host, port=port, pool=self)
            self._queue.put_nowait(cl)
            self._clients.append(cl)

        self._inited = False
        self._closed = False
        self._echo_time = echo_time

    async def _init(self):
        if self._inited:
            return None
        if self._closed:
            raise RadishClientError('Pool is closed')
        connect_tasks = [cl.connect() for cl in self._clients]
        await asyncio.gather(*connect_tasks, loop=self._loop)
        self._inited = True

    def acquire(self):
        return PoolObjContext(self)

    async def _acquire(self):
        self._check_inited()
        print('popped')
        return await self._queue.get()

    def release(self, entity):
        self._check_inited()
        print('released')
        self._queue.put_nowait(entity)

    async def close(self):
        self._check_inited()
        self._closed = True
        coros = [cl.close() for cl in self._clients]
        await asyncio.gather(*coros, loop=self._loop)

    def _check_inited(self):
        if not self._inited:
            raise RadishClientError('Pool is not inited')
        if self._closed:
            raise RadishClientError('Pool is closed')

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


class Client:
    def __init__(self, host, port, pool):
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

    async def execute(self, *args):
        try:
            await process_response(self._stream.writer, args)
            if args[0] != b'QUIT':
                resp = await process_request(self._stream.reader)
            else:
                resp = None
        except RadishConnectionError as e:
            print('error: %s' % e.msg)
            self._pool.close()
            raise RadishClientError(e.msg)
        else:
            return resp


"""
Examples of usage:
"""


async def run_client(pool: Pool, commands: List[List[bytes]]):
    async with pool.acquire() as connection:
        for command in commands:
            response = await connection.execute(*command)
            print(response)


async def run_pool(*commands: List[List[bytes]]):
    async with Pool('127.0.0.1', 7272, 2) as pool:
        coros = [run_client(pool, command) for command in commands]
        await asyncio.gather(*coros)


def run(commands_lists):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_pool(*commands_lists))
    loop.close()


if __name__ == '__main__':
    """ How multiple clients can work in one connection loop: """
    run([
        [
            [b'SET', b'key', b'val'],
            [b'GET', b'key'],
            [b'PING'],
            [b'EXISTS', b'key', b'key', b'nokey'],
            [b'EXISTS', b'key'],
            [b'MSET', b'key1', b'val1', b'key2', b'val2'],
            [b'EXISTS', b'key2'],
            [b'ECHO', b'Hello!'],
            [b'PING', b'Hello?'],
            [b'PING'],
            [b'FLUSHDB'],
        ],
        [
            [b'SET', b'otherkey', b'val'],
            [b'GET', b'otherkey'],
            [b'DEL', b'otherkey'],
        ],
        [
            [b'PING'],
            [b'GET', b'something'],
            [b'DEL', b'some'],
            [b'FLUSHDB'],
        ],

    ])

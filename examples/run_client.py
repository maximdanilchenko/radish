"""
Examples of Radish Client usage with Connection Pooling:
"""
import random
import asyncio
import logging
from typing import List

from radish import client


async def run_client(pool: client.Pool, commands: List[List[bytes]]):
    async with pool.acquire() as connection:
        for command in commands:
            response = await connection.execute(*command)
            logging.debug(response)
            await asyncio.sleep(600)


async def run_pool(*commands: List[List[bytes]]):
    async with client.Pool('127.0.0.1', 7272, 5) as pool:
        coros = [run_client(pool, command) for command in commands]
        await asyncio.gather(*coros)


def run(commands_lists):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_pool(*commands_lists))
    loop.close()


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    """ How multiple clients can work in connection pool for async apps: """
    run(
        [
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
        ] * 5
    )

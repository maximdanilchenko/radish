"""
Example of Radish Client ConnectionPool usage:
"""
import asyncio
import logging
import random

from radish.client import ConnectionPool, Connection

POOL_SETTINGS = dict(host='127.0.0.1', port=7272, min_size=3, max_size=20)
RANDOM_SLEEP = (0, 5)
CLIENTS_COUNT = 10


async def run_client(pool: ConnectionPool):
    async with pool.acquire() as con:  # type: Connection
        random_key = f'key_{random.randint(0, 100)}'
        await con.set(key=random_key, value='my_val')
        assert await con.get(random_key) == b'my_val'
        assert await con.ping() == b'PONG'
        await asyncio.sleep(random.randint(*RANDOM_SLEEP))


async def run_pool():
    async with ConnectionPool(**POOL_SETTINGS) as pool:
        clients = [run_client(pool) for _ in range(CLIENTS_COUNT)]
        await asyncio.gather(*clients)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    """ How multiple clients can work in connection pool for async apps: """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_pool())
    loop.close()

"""
Example of Radish Client Connection usage:
"""
import asyncio
from radish.client import Connection


async def run_client():
    con = Connection(host='127.0.0.1', port=7272)
    assert await con.set('my_key', 'my_val') == 1
    assert await con.get('my_key') == 'my_val'
    assert await con.echo('hello') == 'hello'
    assert await con.delete('my_key') == 1
    await con.close()
    # using "async with" statement:
    async with Connection(host='127.0.0.1', port=7272) as con:
        assert await con.mset(k1=1, k2=b'2', k3='3') == 'OK'
        assert await con.mget('k1', 'k3', 'k2') == [1, '3', b'2']
        assert await con.ping() == 'PONG'
        assert await con.exists('k2') == 1
        assert await con.flush() == 3


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client())
    loop.close()

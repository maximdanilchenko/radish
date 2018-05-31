## Radish - simple Redis-like DB and its client written in python3/asyncio
_Inspired by [this article](http://charlesleifer.com/blog/building-a-simple-redis-server-with-python/)_

![radish](https://user-images.githubusercontent.com/10708076/40731573-0343449c-643a-11e8-95f5-46a9fe9b901b.jpg)

### [Contents](radish):

| Files | Description |
| :--- | :---------- |
| [protocol.py](radish/protocol.py) | Simplified RESP (REdis Serialization Protocol) realization |
| [database](radish/database) | Toy memory Storage with some most common REDIS operations and simple socket Server with asyncio |
| [client](radish/client) | Client Connection and ConnectionPool implementation |


### [Examples](examples) of usage:

##### RadishDB Server:
```python
from radish.database import Server

server = Server(host='127.0.0.1', port=7272)
server.run()
```

##### Client with one connection:
```python
import asyncio
from radish.client import Connection


async def run_client():
    con = Connection(host='127.0.0.1', port=7272)  # host and port where radish db server is running
    await con.connect()
    assert await con.set('my_key', 'my_val') == 1
    assert await con.get('my_key') == b'my_val'
    assert await con.echo('hello') == b'hello'
    assert await con.delete('my_key') == 1
    assert await con.mset(k1=1, k2=b'2', k3='3') == b'OK'
    assert await con.mget('k1', 'k3', 'k2') == [b'1', b'3', b'2']
    assert await con.ping() == b'PONG'
    assert await con.exists('k2') == 1
    assert await con.flush() == 3
    await con.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(run_client())
loop.close()
```

##### Client with connection pooling:
```python
import asyncio
import random

from radish.client import ConnectionPool, Connection


async def run_client(pool: ConnectionPool):
    async with pool.acquire() as con:  # type: Connection
        assert await con.ping() == b'PONG'
        await asyncio.sleep(random.randint(0, 5))


async def run_pool():
    async with ConnectionPool(host='127.0.0.1', port=7272, size=5) as pool:
        clients = [run_client(pool) for _ in range(10)]
        await asyncio.gather(*clients)


loop = asyncio.get_event_loop()
loop.run_until_complete(run_pool())
loop.close()
```

### Why?
After I read [this article](http://charlesleifer.com/blog/building-a-simple-redis-server-with-python/) 
I was inspired to do something like it, but with asyncio, with more commands and 
with whole client stuff (such as connection pool). 
It was interesting for me to understand how redis exchange with 
client apps is made and how these tools work on client side.

Main parts of this work/studying:
- RESP protocol, which can be used for both client and database
- Async socket server based on python3 asyncio
- Toy REDIS-like database - it is toy-database, but interesting for implementation 
and for benchmarking this whole solution
- Client side implementation
- Connection Pool for client. It was most interesting part for me 
and one of the causes I started this repo

### Pypi package/usage in real tasks
While Radish DB is in development it is not recommended to use it in some real tasks. 
There are some things I should do before - benchmarks, tests and some fixes and issues are in backlog to implement.

After all it **is not a database for production apps** - it is redis clone, written in Python. 
But I thing it will be good for prototyping or for small apps 
because of its simple installation and starting - it is lightweight and has no dependencies. 
But overall it will be possible only after benchmarks and tests will be done.

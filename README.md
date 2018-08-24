# Radish 
##### Simple in-memory DB and its client written in python3/asyncio for python3/asyncio 
Supports ```string```, ```bytes```, ```int```, ```list```, ```tuple``` data types  

## Quick start
### Server
##### Run RadishDB Server:
```python
from radish.database import Server

server = Server(host='127.0.0.1', port=7272)
server.run()
```
After that you will see an awesome output: 
```
_____Serving RadishDB on 127.0.0.1:7272_____
 _  ___  _ ___   ___  ___  ___  _  ___  _ _ 
| ||_ _||// __> | . \| . || . \| |/ __>| | |
| | | |   \__ \ |   /|   || | || |\__ \|   |
|_| |_|   <___/ |_\_\|_|_||___/|_|<___/|_|_|
```
That means that server is ready for handling connections.

### Client
##### Client with one connection:
```python
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
        assert await con.mset(k1=1, k2=b'2', k3='3') == b'OK'
        assert await con.mget('k1', 'k3', 'k2') == [1, '3', b'2']
        assert await con.ping() == 'PONG'
        assert await con.exists('k2') == 1
        assert await con.flush() == 3
```

##### Client with connection pooling:
```python
import asyncio

from radish.client import ConnectionPool, Connection


async def run_client(pool: ConnectionPool):
    async with pool.acquire() as con:  # type: Connection
        assert await con.ping() == 'PONG'


async def run_pool():
    async with ConnectionPool(host='127.0.0.1', 
                              port=7272, 
                              min_size=5, 
                              max_size=50) as pool:
        clients = [run_client(pool) for _ in range(1000)]
        await asyncio.gather(*clients)
```

Find more examples [here](examples)

## Contents:

| Files | Description |
| :--- | :---------- |
| [database](radish/database) | Toy memory Storage with some most common operations and socket Server with asyncio |
| [client](radish/client) | Client Connection and ConnectionPool implementations |
| [protocol.py](radish/protocol.py) | Simplified to pythonic one RESP (REdis Serialization Protocol) realization |

## Why?
- After I read [this article](http://charlesleifer.com/blog/building-a-simple-redis-server-with-python/) 
I was inspired to do something like it, but with asyncio and more pythonic, with more commands and 
with whole client stuff (such as connection pool). 
- It was interesting for me to understand how database exchange with 
client apps is made and how these tools work on client side.

Main parts of this work/studying:
- RESP protocol, which is used for both client and database
- Async socket server based on python3/asyncio
- In-memory database - it is toy-database for now, but interesting for implementation 
and for benchmarking this whole solution
- Client side implementation with Async Connection Pool. It was most interesting part for me

## Pypi package/usage in real tasks
While Radish DB is in development it is not recommended to use it in some real tasks. 
There are some things I should do before - benchmarks, tests and some fixes and issues are in backlog to implement.

After all it **is not a database for production apps** - it is redis mini clone, written in Python. 
But I thing it will be good for prototyping or for small apps 
because of its simple installation and starting - it is lightweight and has no dependencies. 
But overall it will be possible only after benchmarks and tests will be done.

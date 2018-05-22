### Simple Redis-like DB and its client with connection pool written in python3/asyncio
_Inspired by [this article](http://charlesleifer.com/blog/building-a-simple-redis-server-with-python/)_

#### Contents:

| File | Description |
| :--- | :---------- |
| [protocol.py](radish/protocol.py) | Simplified RESP (REdis Serialization Protocol) realization |
| [server.py](radish/server.py) | Server based on toy memory storage with some most common REDIS operations |
| [client.py](radish/client.py) | Connection pool implementation |


#### Examples of usage:

| File | Description |
| :--- | :---------- |
| [run_server.py](examples/run_server.py) | Example of running DB server |
| [run_client.py](examples/run_client.py) | Example of running multiple clients in parallel using connection pool |


#### Why?
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

#### Pypi package/usage in real tasks
While Radish DB is in development it is not recommended to use it in some real tasks. 
There are some things I should do before - benchmarks, tests and some fixes and issues are in backlog to implement.

After all it **is not a database for production apps** - it is redis clone, written in Python. 
But I thing it will be good for prototyping or for small apps 
because of its simple installation and starting - it is lightweight and has no dependencies. 
But overall it will be possible after benchmarks and tests will be done.

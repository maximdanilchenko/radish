### Simple REDIS DB implementation written in python3/asyncio | Just for fun
_Inspired by [this article](http://charlesleifer.com/blog/building-a-simple-redis-server-with-python/)_

#### Contents:

| File | Description |
| :--- | :---------- |
| protocol.py | Simplified RESP (REdis Serialization Protocol) realization |
| server.py | Server based on toy memory storage with some most common REDIS operations |
| client.py | Multiple clients emulation |


#### Requires:
- [async_timeout](https://github.com/aio-libs/async-timeout)

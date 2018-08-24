from itertools import chain

from radish.exceptions import RadishClientError


class CommandsMixin:
    """ Mixin for executing commands with high level interface """

    async def execute(self, *_):
        raise NotImplementedError

    async def get(self, key):
        return await self.execute(b"GET", key)

    async def set(self, key, value):
        return await self.execute(b"SET", key, value)

    async def delete(self, key):
        return await self.execute(b"DEL", key)

    async def flushdb(self):
        return await self.execute(b"FLUSHDB")

    flush = flushdb

    async def exists(self, key):
        return await self.execute(b"EXISTS", key)

    async def echo(self, echo):
        return await self.execute(b"ECHO", echo)

    async def ping(self):
        return await self.execute(b"PING")

    async def quit(self):
        return await self.execute(b"QUIT")

    async def mset(self, *args, **kwargs):
        if len(args) % 2:
            raise RadishClientError(
                "Incorrect args number. Should be even (key: value)"
            )
        return await self.execute(b"MSET", *args, *chain(*kwargs.items()))

    async def mget(self, *keys):
        return await self.execute(b"MGET", *keys)

    async def strlen(self, key):
        return await self.execute(b"STRLEN", key)

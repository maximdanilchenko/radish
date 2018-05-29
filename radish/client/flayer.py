from itertools import chain

from radish.exceptions import RadishClientError


class FLayer:

    async def _execute(self, *args):
        raise NotImplementedError

    @staticmethod
    def _to_bytes(arg):
        if isinstance(arg, bytes):
            return arg
        elif isinstance(arg, str):
            return arg.encode()
        elif isinstance(arg, int):
            return b'%d' % arg
        else:
            raise RadishClientError(b'Incorrect execute argument type')

    async def execute(self, *args):
        return await self._execute(*map(self._to_bytes, args))

    async def get(self, key):
        return await self.execute(b'GET', key)

    async def set(self, key, value):
        return await self.execute(b'SET', key, value)

    async def delete(self, key):
        return await self.execute(b'DELETE', key)

    async def flush(self):
        return await self.execute(b'FLUSH')

    async def exists(self, key):
        return await self.execute(b'EXISTS', key)

    async def echo(self, echo):
        return await self.execute(b'ECHO', echo)

    async def ping(self):
        return await self.execute(b'PING')

    async def quit(self):
        return await self.execute(b'QUIT')

    async def mset(self, *args, **kwargs):
        if len(args) % 2:
            raise RadishClientError(
                b'Incorrect args number. Should be even (key: value)')
        return await self.execute(b'MSET', *args, *chain(*kwargs.items()))

    async def mget(self, *keys):
        return await self.execute(b'MGET', *keys)

    async def strlen(self, key):
        return await self.execute(b'STRLEN', key)


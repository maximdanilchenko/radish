import logging
import asyncio

from radish.protocol import (Error, RadishBadRequest, RadishConnectionError,
                             process_reader,
                             process_writer)


__all__ = 'run'


class RadishStore:
    """ Python implementation of REDIS Storage """
    def __init__(self):
        self._store = {}
        self.commands = {
            b'GET': self.get,
            b'SET': self.set,
            b'DEL': self.delete,
            b'FLUSHDB': self.flush,
            b'EXISTS': self.exists,
            b'ECHO': self.echo,
            b'PING': self.ping,
            b'QUIT': self.quit,
            b'MGET': self.mget,
            b'MSET': self.mset,
            b'STRLEN': self.strlen,
        }

    def process_command(self, command, *args):
        try:
            return self.commands[command.upper()](*args)
        except KeyError:
            raise RadishBadRequest(b'Bad command')

    def get(self, *args):
        if len(args) != 1:
            raise RadishBadRequest(b'Wrong number of arguments for GET')
        return self._store.get(args[0])

    def set(self, *args):
        if len(args) != 2:
            raise RadishBadRequest(b'Wrong number of arguments for SET')
        val = args[1]
        if isinstance(val, str):
            val = val.encode()
        elif isinstance(val, int):
            val = b'%d' % val
        self._store[args[0]] = val
        return 1

    def delete(self, *args):
        if len(args) != 1:
            raise RadishBadRequest(b'Wrong number of arguments for GET')
        try:
            del self._store[args[0]]
            return 1
        except KeyError:
            return 0

    def flush(self):
        store_len = len(self._store)
        self._store.clear()
        return store_len

    def exists(self, *args):
        if not args:
            raise RadishBadRequest(b'Wrong number of arguments for EXISTS')
        return sum(1 if key in self._store else 0 for key in args)

    def echo(self, *args):
        if not args:
            raise RadishBadRequest(b'Wrong number of arguments for ECHO')
        return args[0]

    def ping(self, *args):
        if not args:
            return b'PONG'
        return args[0]

    def quit(self, *args):
        raise RadishConnectionError(b'QUIT command')

    def mset(self, *args):
        if not args or len(args) % 2:
            raise RadishBadRequest(b'Wrong number of arguments for MSET')
        lst_it = iter(args)
        for key, val in zip(lst_it, lst_it):
            self.set(key,val)
        return b'OK'

    def mget(self, *args):
        if not args:
            raise RadishBadRequest(b'Wrong number of arguments for MGET')
        return [self._store.get(key) for key in args]

    def strlen(self, *args):
        if len(args) != 1:
            raise RadishBadRequest(b'Wrong number of arguments for STRLEN')
        try:
            return len(self._store[args[0]])
        except KeyError:
            return 0
        except TypeError:
            raise RadishBadRequest(b'Wrong type of value')


store = RadishStore()


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    while 1:
        try:
            request = await process_reader(reader)
            logging.debug('Got request from %s: %s', addr, request)
            if not isinstance(request, list):
                raise RadishBadRequest(b'Bad request format')
            answer = store.process_command(*request)
        except RadishBadRequest as e:
            answer = Error(e.msg)
        except RadishConnectionError:
            writer.close()
            logging.debug('Connection from %s closed', addr)
            break
        logging.debug(answer)
        await process_writer(writer, answer)


def run(host='127.0.0.1', port=7272, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handler, host, port, loop=loop)

    server = loop.run_until_complete(coro)

    print(f'Serving RadishDB on {server.sockets[0].getsockname()}')
    logging.debug(f'Serving RadishDB on {server.sockets[0].getsockname()}')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

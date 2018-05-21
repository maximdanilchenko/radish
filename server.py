import asyncio

from protocol import (Error, RadishBadRequest, RadishConnectionError, RadishProtocol)


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
        }

    def process_command(self, command, *args):
        try:
            return self.commands[command.upper()](*args)
        except KeyError:
            raise RadishBadRequest('Bad command')

    def get(self, *args):
        if len(args) != 1:
            raise RadishBadRequest('Wrong number of arguments for GET')
        return self._store.get(args[0])

    def set(self, *args):
        if len(args) != 2:
            raise RadishBadRequest('Wrong number of arguments for SET')
        self._store[args[0]] = args[1]
        return 1

    def delete(self, *args):
        if len(args) != 1:
            raise RadishBadRequest('Wrong number of arguments for GET')
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
            raise RadishBadRequest('Wrong number of arguments for EXISTS')
        return sum(1 if key in self._store else 0 for key in args)

    def echo(self, *args):
        if not args:
            raise RadishBadRequest('Wrong number of arguments for ECHO')
        return args[0]

    def ping(self, *args):
        if not args:
            return b'PONG'
        return args[0]

    def quit(self, *args):
        raise RadishConnectionError('QUIT command')

    def mset(self, *args):
        if not args or len(args) % 2:
            raise RadishBadRequest('Wrong number of arguments for MSET')
        lst_it = iter(args)
        for key, val in zip(lst_it, lst_it):
            self._store[key] = val

    def mget(self, *args):
        if not args:
            raise RadishBadRequest('Wrong number of arguments for MGET')
        return [self._store.get(key) for key in args]


store = RadishStore()


async def processor(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    proto = RadishProtocol()
    while 1:
        try:
            request = await proto.process_request(reader)
        except RadishConnectionError:
            writer.close()
            print('closed')
            break
        except RadishBadRequest as e:
            answer = Error(e.msg)
        else:
            print(request)
            if not isinstance(request, list):
                answer = Error(b'Bad request format')
                await proto.process_response(writer, answer)
                writer.close()
                break
            try:
                answer = store.process_command(*request)
            except RadishBadRequest as e:
                answer = Error(e.msg)
            except RadishConnectionError:
                writer.close()
                print('closed')
                break
        print(answer)
        await proto.process_response(writer, answer)


def run(host='127.0.0.1', port=7272, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    coro = asyncio.start_server(processor, host, port, loop=loop)

    server = loop.run_until_complete(coro)

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    run()

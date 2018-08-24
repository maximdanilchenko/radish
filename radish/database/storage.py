from radish.exceptions import RadishBadRequest, RadishConnectionError


class RadishStore:

    __slots__ = '_store', 'commands'

    def __init__(self, store_obj: dict=None):
        """
        Python implementation of REDIS Storage (only in-memory)

        :param store_obj: dict like obj for storing storage values
        """
        self._store = store_obj or {}
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
        return sum(key in self._store for key in args)

    def echo(self, *args):
        if len(args) != 1:
            raise RadishBadRequest('Wrong number of arguments for ECHO')
        return args[0]

    def ping(self, *args):
        if len(args) != 1:
            return 'PONG'
        return args[0]

    def quit(self, *args):
        raise RadishConnectionError('QUIT command')

    def mset(self, *args):
        if not args or len(args) % 2:
            raise RadishBadRequest('Wrong number of arguments for MSET')
        lst_it = iter(args)
        for key, val in zip(lst_it, lst_it):
            self.set(key, val)
        return 'OK'

    def mget(self, *args):
        if not args:
            raise RadishBadRequest('Wrong number of arguments for MGET')
        return [self._store.get(key) for key in args]

    def strlen(self, *args):
        if len(args) != 1:
            raise RadishBadRequest('Wrong number of arguments for STRLEN')
        try:
            return len(self._store[args[0]])
        except KeyError:
            return 0
        except TypeError:
            raise RadishBadRequest('Wrong type of value')

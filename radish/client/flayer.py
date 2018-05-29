

class FLayer:

    def _execute(self, *args):
        raise NotImplementedError

    def to_bytes(self, arg):
        if isinstance(arg, bytes):
            return arg
        elif isinstance(arg, str):
            return arg.encode()
        elif isinstance(arg, int):
            return b'%d' % arg
        else:
            raise Exception

    def execute(self, cmd, *args):
        return self._execute(cmd, *map(self.to_bytes, args))

    def get(self, key):
        self.execute(b'GET', key)

    def set(self, key, value):
        self.execute(b'SET', key, value)

    def delete(self, key):
        self.execute(b'DELETE')

    def flush(self, key):
        self.execute(b'FLUSH')

    def exists(self, key):
        self.execute(b'EXISTS')

    def echo(self, key):
        self.execute(b'ECHO')

    def ping(self, key):
        self.execute(b'PING')

    def quit(self, key):
        self.execute(b'QUIT')

    def mset(self, key):
        self.execute(b'MSET')

    def mget(self, key):
        self.execute(b'MGET')

    def strlen(self, key):
        self.execute(b'STRLEN')


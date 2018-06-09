import logging
import asyncio

from radish.protocol import Error, process_reader, process_writer
from radish.exceptions import RadishBadRequest, RadishConnectionError

from .storage import RadishStore


class Server:

    def __init__(self, host: str='127.0.0.1', port: int=7272, storage: RadishStore=None):
        self.host = host
        self.port = port
        self.storage = storage or RadishStore()

    async def handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        address = writer.get_extra_info('peername')
        while 1:
            try:
                request = await process_reader(reader)
                logging.debug(f'Got request from {address}: {request}')
                if not isinstance(request, list):
                    raise RadishBadRequest(b'Bad request format')
                answer = self.storage.process_command(*request)
            except RadishBadRequest as e:
                answer = Error(e.msg)
            except (RadishConnectionError, ConnectionError):
                writer.close()
                logging.debug(f'Connection from  {address} CLOSED')
                break
            logging.debug(f'Sent response to {address}: {answer}')
            await process_writer(writer, answer)

    def run(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        coro = asyncio.start_server(self.handler,
                                    self.host,
                                    self.port,
                                    loop=loop)

        server = loop.run_until_complete(coro)
        host, port = server.sockets[0].getsockname()
        address = f'Serving RadishDB on {host}:{port}'
        print(f'\n{address:_^44}')
        print('\n'.join([
                    ' _  ___  _ ___   ___  ___  ___  _  ___  _ _ ',
                    '| ||_ _||// __> | . \| . || . \| |/ __>| | |',
                    '| | | |   \__ \ |   /|   || | || |\__ \|   |',
                    '|_| |_|   <___/ |_\_\|_|_||___/|_|<___/|_|_|',
                    ''
                     ]))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

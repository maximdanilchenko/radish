import logging
import asyncio

from radish.protocol import Error, process_reader, process_writer
from radish.exceptions import RadishBadRequest, RadishConnectionError

from .storage import RadishStore

__all__ = ['run']


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

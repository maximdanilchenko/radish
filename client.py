import asyncio

from protocol import RadishProtocol, RadishConnectionError


async def radish_client(messages: list, loop):
    proto = RadishProtocol()
    reader, writer = await asyncio.open_connection('127.0.0.1', 7272,
                                                   loop=loop)
    try:
        for message in messages:
            print('Send: %r' % message)
            await proto.process_response(writer, message)
            print('Received: %r' % await proto.process_request(reader))
    except RadishConnectionError as e:
        print(e)
    print('Close the socket')
    writer.close()


def run_clients(clients):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([radish_client(messages, loop) for messages in clients]))
    loop.close()


if __name__ == '__main__':
    """ How multiple clients can work: """
    run_clients([
        [
            [b'SET', b'key', b'val'],
            [b'GET', b'key'],
            [b'PING'],
            [b'EXISTS', b'key', b'key', b'nokey'],
            [b'EXISTS', b'key'],
            [b'MSET', b'key1', b'val1', b'key2', b'val2'],
            [b'EXISTS', b'key2'],
            [b'ECHO', b'Hello!'],
            [b'PING', b'Hello?'],
            [b'PING'],
            [b'FLUSHDB'],
            [b'QUIT'],
        ],
        [
            [b'SET', b'otherkey', b'val'],
            [b'GET', b'otherkey'],
            [b'DEL', b'otherkey'],
        ],
        [
            [b'PING'],
            [b'GET', b'something'],
            [b'DEL', b'some'],
            [b'FLUSHDB'],
            [b'QUIT'],
        ],

    ])

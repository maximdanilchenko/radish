from typing import Union
import asyncio
from collections import namedtuple
import async_timeout

Error = namedtuple('Error', ['message'])


CLIENT_CONNECTION_TIMEOUT = 300


class RadishError(Exception):
    def __init__(self, msg: Union[str, bytes]=b'Radish Protocol Error'):
        if isinstance(msg, str):
            self.msg = msg.encode()
        else:
            self.msg = msg


class RadishBadRequest(RadishError):
    """ Bad request error """


class RadishProtocolError(RadishError):
    """ Protocol error """


class RadishConnectionError(RadishError):
    """ Connection Error """


class RadishProtocol:
    """
    Implementing Redis Serialization Protocol (RESP)
        The way RESP is used in Redis as a request-response protocol is the following:
            - Clients send commands to a Redis server as a RESP Array of Bulk Strings.
            - The server replies with one of the RESP types according to the command implementation.
        In RESP, the type of some data depends on the first byte:
            - For Simple Strings the first byte of the reply is "+"
            - For Errors the first byte of the reply is "-"
            - For Integers the first byte of the reply is ":"
            - For Bulk Strings the first byte of the reply is "$"
            - For Arrays the first byte of the reply is "*"
            Additionally RESP is able to represent a Null value using a special variation of Bulk Strings or Array
        In RESP different parts of the protocol are always terminated with "\r\n"
    Examples:
        Simple string example: "+OK\r\n"
        Error example: "-Error message\r\n"
        Integer example: ":1134\r\n"
        Bulk string examples: "$6\r\nfoobar\r\n", "$0\r\n\r\n"
            Null: "$-1\r\n"
        Array examples:
            Empty: "*0\r\n"
            [b'foo', b'bar']: "*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
            [1, 2, 3]: "*3\r\n:1\r\n:2\r\n:3\r\n"
            Null array: "*-1\r\n"
            [b'foo', nil, b'bar']: *3\r\n$3\r\nfoo\r\n$-1\r\n$3\r\nbar\r\n
    """
    def __init__(self):
        self.data_processors = {
            b'+': self.process_simple_string,
            b'-': self.process_error,
            b':': self.process_integer,
            b'$': self.process_string,
            b'*': self.process_array
        }

    async def process_request(self, reader: asyncio.StreamReader):
        try:
            async with async_timeout.timeout(CLIENT_CONNECTION_TIMEOUT):
                command = await reader.read(1)
        except asyncio.TimeoutError:
            raise RadishConnectionError('Timeout error')
        if not command:
            raise RadishConnectionError('Empty request')
        try:
            return await self.data_processors[command](reader)
        except KeyError:
            raise RadishBadRequest('Bad first byte')

    async def process_simple_string(self, reader):
        return (await reader.readline()).strip()

    async def process_error(self, reader):
        return Error((await reader.readline()).strip())

    async def process_integer(self, reader):
        return int((await reader.readline()).strip())

    async def process_string(self, reader):
        length = int((await reader.readline()).strip())
        if length == -1:
            return None
        return (await reader.read(length+2))[:-2]

    async def process_array(self, reader):
        num_elements = int((await reader.readline()).strip())
        if num_elements == -1:
            return [None]
        if num_elements < 0:
            raise RadishBadRequest('Bad array length')
        return [(await self.process_request(reader)) for _ in range(num_elements)]

    async def process_response(self, writer, data):
        self._write_response(writer, data)
        await writer.drain()

    def _write_response(self, writer: asyncio.StreamWriter, data: Union[bytes, int, Error, list, tuple]):
        if isinstance(data, bytes):
            writer.write(b'$%d\r\n%s\r\n' % (len(data), data))
        elif isinstance(data, int):
            writer.write(b':%d\r\n' % data)
        elif isinstance(data, Error):
            writer.write(b'-%s\r\n' % data.message)
        elif isinstance(data, (list, tuple)):
            writer.write(b'*%d\r\n' % len(data))
            for item in data:
                self._write_response(writer, item)
        elif data is None:
            writer.write(b'$-1\r\n')
        else:
            raise RadishProtocolError('unrecognized type: %s' % type(data))

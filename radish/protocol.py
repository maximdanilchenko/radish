"""
Implementing Redis Serialization Protocol (RESP). Can be used for both server and client sides.
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

from typing import Union
import asyncio
from collections import namedtuple

__all__ = ['Error',
           'RadishBadRequest',
           'RadishConnectionError',
           'RadishError',
           'RadishProtocolError',
           'process_reader',
           'process_writer']


Error = namedtuple('Error', ['message'])

CLIENT_CONNECTION_TIMEOUT = 300


class RadishError(Exception):
    def __init__(self, msg: Union[str, bytes] = b'Radish Error'):
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


async def process_reader(reader: asyncio.StreamReader):
    try:
        command = await asyncio.wait_for(reader.read(1), CLIENT_CONNECTION_TIMEOUT)
    except asyncio.TimeoutError:
        raise RadishConnectionError(b'Timeout error')
    if not command:
        raise RadishConnectionError(b'Empty request')
    try:
        return await {
            b'+': _process_simple_string,
            b'-': _process_error,
            b':': _process_integer,
            b'$': _process_string,
            b'*': _process_array
        }[command](reader)
    except KeyError:
        raise RadishBadRequest(b'Bad first byte')


async def _process_simple_string(reader: asyncio.StreamReader):
    return (await reader.readline()).strip()


async def _process_error(reader: asyncio.StreamReader):
    return Error((await reader.readline()).strip())


async def _process_integer(reader: asyncio.StreamReader):
    return int((await reader.readline()).strip())


async def _process_string(reader: asyncio.StreamReader):
    length = int((await reader.readline()).strip())
    if length == -1:
        return None
    return (await reader.read(length + 2))[:-2]


async def _process_array(reader: asyncio.StreamReader):
    num_elements = int((await reader.readline()).strip())
    if num_elements == -1:
        return [None]
    if num_elements < 0:
        raise RadishBadRequest(b'Bad array length')
    return [(await process_reader(reader)) for _ in range(num_elements)]


async def process_writer(writer: asyncio.StreamWriter,
                         data: Union[bytes,
                                     int,
                                     Error,
                                     list,
                                     tuple]):
    _write_response(writer, data)
    await writer.drain()


def _write_response(writer: asyncio.StreamWriter,
                    data: Union[bytes,
                                int,
                                Error,
                                list,
                                tuple]):
    if isinstance(data, bytes):
        writer.write(b'$%d\r\n%s\r\n' % (len(data), data))
    elif isinstance(data, int):
        writer.write(b':%d\r\n' % data)
    elif isinstance(data, Error):
        writer.write(b'-%s\r\n' % data.message)
    elif isinstance(data, (list, tuple)):
        writer.write(b'*%d\r\n' % len(data))
        for item in data:
            _write_response(writer, item)
    elif data is None:
        writer.write(b'$-1\r\n')
    else:
        raise RadishProtocolError(b'Unrecognized type: %s' % type(data))
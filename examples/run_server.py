"""
Examples of Radish DB usage:
"""
import logging
import asyncio
from radish.database import server

SERVER_SETTINGS = dict(host='127.0.0.1', port=7272)

# Try to use UVloop:
try:
    import uvloop
except ImportError:
    logging.warn('Could not import uvloop. Using custom asyncio loop')
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    server.run(**SERVER_SETTINGS)

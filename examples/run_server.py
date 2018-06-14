"""
Example of Radish DB usage:
"""
import logging
from radish.database import Server


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    server = Server(host='127.0.0.1', port=7272, closing_delay=300)
    server.run()

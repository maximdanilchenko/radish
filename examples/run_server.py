"""
Example of Radish DB usage:
"""
from radish.database import Server


if __name__ == '__main__':
    server = Server(host='127.0.0.1', port=7272)
    server.run()

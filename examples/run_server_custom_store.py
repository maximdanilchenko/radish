"""
Example of Radish DB usage with own storage object:
"""
from radish.database import Server, RadishStore


if __name__ == '__main__':
    my_storage = {}
    radish_store = RadishStore(my_storage)
    server = Server(host='127.0.0.1', port=7272, storage=radish_store)
    server.run()

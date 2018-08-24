from typing import Union


class RadishError(Exception):

    def __init__(self, msg: Union[str, bytes] = 'Radish Error'):
        self.msg = msg


class RadishBadRequest(RadishError):
    """ Bad request error """


class RadishProtocolError(RadishError):
    """ Protocol error """


class RadishConnectionError(RadishError):
    """ Connection Error """


class RadishClientError(RadishError):
    """ Client Error """

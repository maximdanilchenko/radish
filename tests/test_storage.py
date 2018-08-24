import pytest

from radish.database import RadishStore
from radish.exceptions import RadishConnectionError, RadishBadRequest


@pytest.fixture
def db():
    return RadishStore()


def test_bad_command(db: RadishStore):
    try:
        db.process_command(b"BAD")
    except Exception as e:
        exc = e
    else:
        exc = None
    assert isinstance(exc, RadishBadRequest)


def test_set(db: RadishStore):
    assert db.set(b"key", b"val") == 1
    assert db._store == {b"key": b"val"}


def test_get(db: RadishStore):
    assert db.get(b"key") is None
    db._store = {b"key": b"val"}
    assert db.get(b"key") == b"val"


def test_delete(db: RadishStore):
    assert db.delete(b"key") == 0
    db._store = {b"key": b"val"}
    assert db.delete(b"key") == 1


def test_flush(db: RadishStore):
    assert db.flush() == 0
    db._store = {b"k1": b"1", b"k2": b"1", b"k3": b"1"}
    assert db.flush() == 3
    assert db._store == {}


def test_exists(db: RadishStore):
    db._store = {b"k1": b"1", b"k2": b"1", b"k3": b"1"}
    assert db.exists(b"key") == 0
    assert db.exists(b"k1") == 1
    assert db.exists(b"k1", b"k2") == 2
    assert db.exists(b"k1", b"k2", b"key") == 2


def test_echo(db: RadishStore):
    assert db.echo(b"hello") == b"hello"


def test_ping(db: RadishStore):
    assert db.ping() == b"PONG"


def test_quit(db: RadishStore):
    try:
        db.quit()
    except Exception as e:
        exc = e
    else:
        exc = None
    assert isinstance(exc, RadishConnectionError)


def test_mset(db: RadishStore):
    assert db.mset(b"key", b"val", b"key2", b"val2") == b"OK"
    assert db._store == {b"key": b"val", b"key2": b"val2"}
    try:
        db.mset(b"key2", b"val", b"key4")
    except Exception as e:
        exc = e
    else:
        exc = None
    assert isinstance(exc, RadishBadRequest)
    assert db._store == {b"key": b"val", b"key2": b"val2"}


def test_mget(db: RadishStore):
    db._store = {b"k1": b"1", b"k2": b"2", b"k3": b"3"}
    assert db.mget(b"k2", b"k1") == [b"2", b"1"]
    assert db.mget(b"k2", b"k5") == [b"2", None]


def test_strlen(db: RadishStore):
    db._store = {b"k1": b"Hello, I am byte string"}
    assert db.strlen(b"k1") == 23
    assert db.strlen(b"k3") == 0

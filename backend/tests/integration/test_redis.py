import os
import uuid

import redis


def test_redis_connection():
    client = redis.Redis.from_url(
        os.environ.get(
            "REDIS_URL",
            "redis://127.0.0.1:6380/0",
        )
    )

    assert client.ping() is True


def test_redis_set_get_delete():
    client = redis.Redis.from_url(
        os.environ.get(
            "REDIS_URL",
            "redis://127.0.0.1:6380/0",
        )
    )

    key = f"test:fcbukhara:{uuid.uuid4()}"

    try:
        client.set(key, "working", ex=30)
        assert client.get(key) == b"working"
    finally:
        client.delete(key)

# -*- coding: utf-8 -*-

import time

import pytest
from django.core.cache import cache

from jnt_django_toolbox.context_managers import global_lock
from jnt_django_toolbox.context_managers.global_lock import (  # noqa: WPS450
    LOCK_EXPIRE,
    _build_lock_cache_key,
)


@pytest.fixture(autouse=True)
def _setup_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "KEY_PREFIX": "test",
        },
    }

    yield

    cache.clear()


class _ExecuteContext:
    acquired = False


@pytest.fixture()
def context():
    return _ExecuteContext()


def test_simple(context):
    def demo():  # noqa: WPS430
        with global_lock("test_lock") as acquired:
            context.acquired = acquired

    demo()
    assert context.acquired
    assert cache.get(_build_lock_cache_key("test_lock")) is None


def test_many_executes(context):
    def demo():  # noqa: WPS430
        with global_lock("test_lock") as acquired:
            context.acquired = acquired

    demo()
    assert context.acquired
    assert cache.get(_build_lock_cache_key("test_lock")) is None

    demo()
    assert context.acquired
    assert cache.get(_build_lock_cache_key("test_lock")) is None


def test_with_exception(context):
    def demo():  # noqa: WPS430
        with global_lock("test_lock") as acquired:
            if acquired:
                raise Exception("test")

    with pytest.raises(Exception, match="test"):
        demo()

    assert cache.get(_build_lock_cache_key("test_lock")) is None


def test_already_runned(context):
    def demo():  # noqa: WPS430
        with global_lock("test_lock") as acquired:
            context.acquired = acquired

    cache_key = _build_lock_cache_key("test_lock")
    cache.add(cache_key, 1, LOCK_EXPIRE)

    demo()
    assert not context.acquired
    assert cache.get(cache_key) == 1


def test_already_runned_expired(context):
    def demo():  # noqa: WPS430
        with global_lock("test_lock") as acquired:
            context.acquired = acquired

    cache.add(_build_lock_cache_key("test_lock"), 1, 1)

    time.sleep(1)

    demo()

    assert context.acquired
    assert cache.get(_build_lock_cache_key("test_lock")) is None

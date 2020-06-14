# -*- coding: utf-8 -*-

import math

import pytest
from django.db import connection, models
from django.db.models import F
from django.db.models.fields import BigIntegerField

from jnt_django_toolbox.models.fields import BitField
from tests.models import BitFieldTestModel


def test_basic(db):
    """Create instance and make sure flags are working properly."""
    instance = BitFieldTestModel.objects.create(flags=1)
    assert instance.flags.FLAG_0
    assert not instance.flags.FLAG_1
    assert not instance.flags.FLAG_2
    assert not instance.flags.FLAG_3


def test_negative(db):
    """Creating new instances shouldn't allow negative values."""
    instance = BitFieldTestModel.objects.create(flags=-1)
    assert instance.flags._value == 15
    assert instance.flags.FLAG_0
    assert instance.flags.FLAG_1
    assert instance.flags.FLAG_2
    assert instance.flags.FLAG_3

    assert BitFieldTestModel.objects.filter(flags=15).count() == 1
    assert not BitFieldTestModel.objects.filter(flags__lt=0).exists()


def test_negative_in_raw_sql(db):
    """Creating new instances shouldn't allow negative values."""
    cursor = connection.cursor()
    flags_field = BitFieldTestModel._meta.get_field("flags")
    flags_db_column = flags_field.db_column or flags_field.name
    cursor.execute(
        "INSERT INTO {0} ({1}) VALUES (-1)".format(
            BitFieldTestModel._meta.db_table, flags_db_column,
        ),
    )
    # There should only be the one row we inserted through the cursor.
    instance = BitFieldTestModel.objects.get(flags=-1)
    assert instance.flags.FLAG_0
    assert instance.flags.FLAG_1
    assert instance.flags.FLAG_2
    assert instance.flags.FLAG_3
    instance.save()

    assert BitFieldTestModel.objects.filter(flags=15).count() == 1
    assert not BitFieldTestModel.objects.filter(flags__lt=0).exists()


def test_select(db):
    BitFieldTestModel.objects.create(flags=3)
    assert BitFieldTestModel.objects.filter(
        flags=BitFieldTestModel.flags.FLAG_1,
    ).exists()
    assert BitFieldTestModel.objects.filter(
        flags=BitFieldTestModel.flags.FLAG_0,
    ).exists()
    assert not BitFieldTestModel.objects.exclude(
        flags=BitFieldTestModel.flags.FLAG_0,
    ).exists()
    assert not BitFieldTestModel.objects.exclude(
        flags=BitFieldTestModel.flags.FLAG_1,
    ).exists()


def test_update(db):
    instance = BitFieldTestModel.objects.create(flags=0)
    assert not instance.flags.FLAG_0

    BitFieldTestModel.objects.filter(pk=instance.pk).update(
        # flags=bitor(F("flags"), BitFieldTestModel.flags.FLAG_1),
        flags=F("flags").bitor(BitFieldTestModel.flags.FLAG_1),
    )
    instance = BitFieldTestModel.objects.get(pk=instance.pk)
    assert instance.flags.FLAG_1

    BitFieldTestModel.objects.filter(pk=instance.pk).update(
        flags=F("flags").bitor(
            (~BitFieldTestModel.flags.FLAG_0 | BitFieldTestModel.flags.FLAG_3),
        ),
    )
    instance = BitFieldTestModel.objects.get(pk=instance.pk)
    assert not instance.flags.FLAG_0
    assert instance.flags.FLAG_1
    assert instance.flags.FLAG_3
    assert not BitFieldTestModel.objects.filter(
        flags=BitFieldTestModel.flags.FLAG_0,
    ).exists()

    BitFieldTestModel.objects.filter(pk=instance.pk).update(
        flags=F("flags").bitand(~BitFieldTestModel.flags.FLAG_3),
    )
    instance = BitFieldTestModel.objects.get(pk=instance.pk)
    assert not instance.flags.FLAG_0
    assert instance.flags.FLAG_1
    assert not instance.flags.FLAG_3


def test_update_with_handler(db):
    instance = BitFieldTestModel.objects.create(flags=0)
    assert not instance.flags.FLAG_0

    instance.flags.FLAG_1 = True

    BitFieldTestModel.objects.filter(pk=instance.pk).update(
        flags=F("flags").bitor(instance.flags),
    )
    instance = BitFieldTestModel.objects.get(pk=instance.pk)
    assert instance.flags.FLAG_1


def test_negate(db):
    BitFieldTestModel.objects.create(
        flags=BitFieldTestModel.flags.FLAG_0 | BitFieldTestModel.flags.FLAG_1,
    )
    BitFieldTestModel.objects.create(flags=BitFieldTestModel.flags.FLAG_1)
    assert (
        BitFieldTestModel.objects.filter(
            flags=~BitFieldTestModel.flags.FLAG_0,
        ).count()
        == 1
    )
    assert not BitFieldTestModel.objects.filter(
        flags=~BitFieldTestModel.flags.FLAG_1,
    ).exists()
    assert (
        BitFieldTestModel.objects.filter(
            flags=~BitFieldTestModel.flags.FLAG_2,
        ).count()
        == 2
    )


def test_default_value(db):
    instance = BitFieldTestModel.objects.create()
    assert instance.flags.FLAG_0
    assert instance.flags.FLAG_1
    assert not instance.flags.FLAG_2
    assert not instance.flags.FLAG_3


def test_binary_capacity(db):
    # Local maximum value, slow canonical algorithm
    MAX_COUNT = int(math.floor(math.log(BigIntegerField.MAX_BIGINT, 2)))

    # Big flags list
    flags = ["f{0}".format(i) for i in range(100)]

    BitField(flags=flags[:MAX_COUNT])

    with pytest.raises(ValueError, match="Too many flags"):
        BitField(flags=flags[: (MAX_COUNT + 1)])


def test_dictionary_init(db):
    flags = {
        0: "zero",
        1: "first",
        10: "tenth",
        2: "second",
        "wrongkey": "wrongkey",
        100: "bigkey",
        -100: "smallkey",
    }

    bf = BitField(flags)

    assert bf.flags == [
        "zero",
        "first",
        "second",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "tenth",
    ]

    with pytest.raises(ValueError, match="Wrong keys or empty dictionary"):
        BitField(flags={})

    with pytest.raises(ValueError, match="Wrong keys or empty dictionary"):
        BitField(flags={"wrongkey": "wrongkey"})

    with pytest.raises(ValueError, match="Wrong keys or empty dictionary"):
        BitField(flags={"1": "non_int_key"})


class DefaultKeyNamesModel(models.Model):
    flags = BitField(
        flags=("FLAG_0", "FLAG_1", "FLAG_2", "FLAG_3"),
        default=("FLAG_1", "FLAG_2"),
    )


def test_defaults_as_key_names(db):
    field = DefaultKeyNamesModel._meta.get_field("flags")
    assert (
        field.default
        == DefaultKeyNamesModel.flags.FLAG_1
        | DefaultKeyNamesModel.flags.FLAG_2
    )

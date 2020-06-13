# -*- coding: utf-8 -*-

from contextlib import suppress

from django.urls import NoReverseMatch, reverse


def admin_change_url(instance):
    return reverse(
        "admin:{0}_{1}_change".format(
            instance._meta.app_label, instance._meta.model.__name__.lower(),
        ),
        args=(instance.pk,),
    )


def admin_changelist_url(model):
    return reverse(
        "admin:{0}_{1}_changelist".format(
            model._meta.app_label, model.__name__.lower(),
        ),
    )


def admin_autocomplete_url(model):
    with suppress(NoReverseMatch):
        return reverse(
            "admin:{0}_{1}_autocomplete".format(
                model._meta.app_label, model.__name__.lower(),
            ),
        )
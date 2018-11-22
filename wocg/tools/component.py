# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import django
django.setup()  # noqa: E402

from weblate.addons.models import Addon


def copy_installed_addons(src_component_pk, dest_component):
    addons_to_install = Addon.objects.filter(component=src_component_pk)
    for addon_to_install in addons_to_install:
        addon_to_install.pk = None
        addon_to_install.component = dest_component
        addon_to_install.save()

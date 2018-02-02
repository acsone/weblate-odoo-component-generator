# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

import os

MANIFEST_NAMES = ('__openerp__.py', '__manifest__.py', '__terp__.py')


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def get_translatable_addons(addons_dirs):
    res = {}
    for addons_dir in addons_dirs:
        for addon_name in os.listdir(addons_dir):
            addon_dir = os.path.join(addons_dir, addon_name)
            manifest_path = get_manifest_path(addon_dir)
            if not manifest_path:
                continue
            i18n_dir = os.path.join(addon_dir, 'i18n')
            if not os.path.isdir(i18n_dir):
                continue
            pot_file = False
            po_file = False
            for file in os.listdir(i18n_dir):
                if file.endswith(".pot"):
                    pot_file = file
                if file.endswith(".po"):
                    po_file = True
                if po_file and pot_file:
                    break
            if not pot_file or not po_file:
                continue
            res[addon_name] = addon_dir
    return res

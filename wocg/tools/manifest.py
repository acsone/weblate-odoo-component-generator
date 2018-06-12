# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

import ast
import os

MANIFEST_NAMES = ('__openerp__.py', '__manifest__.py', '__terp__.py')


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def parse_manifest(s):
    return ast.literal_eval(s)


def get_translatable_addons(repository_dir, addons_subdirectory=None):
    """
    This method builds a dictionary of all installable addons which contains a
    i18n folder with a .pot file in the specified
    addons directory or in the default addons directory.
    :param repository_dir: path to the git repository
    :param addons_subdirectory: path to the addons directory
    :return: Dictionary like: {'addon_name': (addons_directory, manifest)}
    where manifest is a dictionary.
    """
    res = {}
    addons_dir = os.path.join(repository_dir, addons_subdirectory or '')
    for addon_name in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_name)
        manifest_path = get_manifest_path(addon_dir)
        if not manifest_path:
            continue
        with open(manifest_path) as f:
            manifest = parse_manifest(f.read())
        if not manifest.get('installable', True):
            continue
        i18n_dir = os.path.join(addon_dir, 'i18n')
        if not os.path.isdir(i18n_dir):
            continue
        pot_filepath = os.path.join(i18n_dir, addon_name + '.pot')
        if not os.path.isfile(pot_filepath):
            continue
        res[addon_name] = (addon_dir, manifest)
    return res

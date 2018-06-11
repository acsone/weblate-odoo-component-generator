# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

import django
django.setup()

import os
import re
import logging

from django.conf import settings
from weblate.trans.models import Project

from .manifest import get_translatable_addons


logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - WOCG : %(message)s'))
logger.addHandler(ch)

GIT_URL_RE = re.compile(r"git@.*:.*/.*")

FILEMASK_RE = re.compile(
    r"^(?P<addons_dir>.*/)?(?P<addon_name>.*?)/i18n/\*\.po$")


def _get_main_component(project):
    main_component = False
    for component in project.component_set.all():
        if GIT_URL_RE.match(component.repo):
            main_component = component
            break
    return main_component


def _get_all_components_slug(project):
    components_slug = []
    for component in project.component_set.all():
        components_slug.append(component.slug)
    return components_slug


def _get_component_name(project, addon):
    return "%s-%s" % (project.name, addon)


def _get_component_slug(project, addon):
    return "%s-%s" % (project.slug, addon)


def main():
    all_projects = Project.objects.prefetch_related('source_language')

    data_dir = settings.DATA_DIR
    svn_dir = os.path.join(data_dir, 'vcs')

    for project in all_projects:
        logger.info('Begin generation for project %s', project.name)
        main_component = _get_main_component(project)
        if not main_component:
            logger.info(
                'Main component not found for project %s' % project.name)
            continue
        logger.info('Main component found for project %s : %s' % (
            project.name, main_component.name))
        repo = 'weblate://%s/%s' % (project.slug, main_component.slug)
        logger.info("*** %s", main_component.filemask)
        mo = FILEMASK_RE.match(main_component.filemask)
        if not mo:
            logger.info("Filemask doesn't match structure "
                        "ADDONS_DIR_PATH/MODULE_NAME/*.po")
            continue
        groups = mo.groupdict()
        main_component_addon_name = groups['addon_name']
        addons_dir = groups['addons_dir'] or '.'
        addons_dir_path = os.path.join(
            svn_dir, project.slug, main_component.slug, addons_dir)
        existing_components_slug = _get_all_components_slug(project)
        addons = get_translatable_addons(addons_dirs=[addons_dir_path])
        main_filemask = main_component.filemask
        for addon, addon_dir in addons.items():
            addon_component_name = _get_component_name(project, addon)
            addon_component_slug = _get_component_slug(project, addon)
            if addon_component_slug in existing_components_slug:
                logger.info('component already exist for addon %s : %s' % (
                    addon, addon_component_slug))
                continue
            logger.info('Begin generation for addon %s' % addon)
            filemask = main_filemask.replace(main_component_addon_name, addon)
            logger.info('New filemask %s' % filemask)
            new_component = main_component
            new_component.pk = None
            new_component.name = addon_component_name
            new_component.slug = addon_component_slug
            new_component.filemask = filemask
            new_component.repo = repo
            new_component.save()
    exit(0)

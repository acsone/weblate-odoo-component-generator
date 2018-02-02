# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

import django
django.setup()

import os
import re
import logging

from django.conf import settings
from weblate.trans.models import Project, SubProject

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
    r"^(?P<addons_dir>.*)/(?P<addon_name>.*?)/i18n/\*\.po$")


def _get_main_subproject(project):
    main_subproject = False
    for sub_project in project.subproject_set.all():
        if GIT_URL_RE.match(sub_project.repo):
            main_subproject = sub_project
            break
    return main_subproject


def _get_all_subprojects_slug(project):
    sub_projects_slug = []
    for sub_project in project.subproject_set.all():
        sub_projects_slug.append(sub_project.slug)
    return sub_projects_slug


def _get_slug_name(project, addon):
    return "%s-%s" % (project.slug, addon)


def main():
    all_projects = Project.objects.prefetch_related('source_language')

    data_dir = settings.DATA_DIR
    svn_dir = os.path.join(data_dir, 'vcs')

    for project in all_projects:
        logger.info('Begin generation for project %s', project.name)
        main_subproject = _get_main_subproject(project)
        if not main_subproject:
            logger.info(
                'Main component not found for project %s' % project.name)
            continue
        logger.info('Main component found for project %s : %s' % (
            project.name, main_subproject.name))
        repo = 'weblate://%s/%s' % (project.slug, main_subproject.slug)
        mo = FILEMASK_RE.match(main_subproject.filemask)
        if not mo:
            logger.info("Filemask doesn't match structure "
                        "ADDONS_DIR_PATH/MODULE_NAME/*.po")
            continue
        groups = mo.groupdict()
        main_subproject_addon_name = groups['addon_name']
        addons_dir = groups['addons_dir']
        addons_dir_path = os.path.join(
            svn_dir, project.slug, main_subproject.slug, addons_dir)
        existing_sub_projects_slug = _get_all_subprojects_slug(project)
        addons = get_translatable_addons(addons_dirs=[addons_dir_path])
        main_filemask = main_subproject.filemask
        for addon, addon_dir in addons.items():
            addon_subproject_slug = _get_slug_name(project, addon)
            if addon_subproject_slug in existing_sub_projects_slug:
                logger.info('component already exist for addon %s : %s' % (
                    addon, addon_subproject_slug))
                continue
            logger.info('Begin generation for addon %s' % addon)
            filemask = main_filemask.replace(main_subproject_addon_name, addon)
            logger.info('New filemask %s' % filemask)
            new_subproject = main_subproject
            new_subproject.pk = None
            new_subproject.name = addon_subproject_slug
            new_subproject.slug = addon_subproject_slug
            new_subproject.filemask = filemask
            new_subproject.repo = repo
            new_subproject.save()
    exit(0)

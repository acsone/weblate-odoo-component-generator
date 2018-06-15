# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import re
from urlparse import urljoin

import click
import giturlparse

import django
django.setup()

from weblate.addons.models import Addon
from weblate.trans.models import Project, Component

from .tools.git_utils import git_clone
from .tools.helper import get_component_slug, get_component_name
from .tools.logger import get_logger
from .tools.manifest import get_translatable_addons

logger = get_logger()


def get_project_name(repository, branch):
    repo_name = repository.split('/')[-1].replace('.git', '')
    return '%s-%s' % (repo_name, branch)


def get_project_slug(project_name):
    project_slug = re.sub("[^A-Za-z0-9-]", "-", project_name)
    return project_slug


def create_project(
        repository, branch, tmpl_component_slug,
        addons_subdirectory=None, git_export_base_url=None):
    project_name = get_project_name(repository, branch)

    logger.info("Project name is %s", project_name)

    try:
        Project.objects.get(name=project_name)
        logger.info("Project %s already exists.", project_name)
    except Project.DoesNotExist:
        repo_dir = git_clone(repository, branch)
        addons = get_translatable_addons(
            repo_dir, addons_subdirectory=addons_subdirectory)

        if not addons:
            logger.info("No addons found in %s %s", repository, branch)
            return

        logger.info("Going to create Project %s.", project_name)
        addon_name = next(iter(addons.keys()))
        new_project = get_new_project(project_name, repository)

        try:
            get_new_component(
                new_project, repository, branch, addon_name,
                tmpl_component_slug,
                addons_subdirectory=addons_subdirectory,
                git_export_base_url=git_export_base_url,
            )
        except Exception as e:
            logger.exception(e)
            new_project.delete()


def get_new_project(project_name, repository):
    new_project = Project()
    new_project.name = project_name
    new_project.slug = get_project_slug(project_name)
    new_project.web = giturlparse.parse(repository).url2https
    new_project.enable_review = True
    new_project.set_translation_team = False
    new_project.save()
    return new_project


def get_new_component(
        project, repository, branch, addon_name, tmpl_component_slug,
        addons_subdirectory=None, git_export_base_url=None):
    po_file_mask = '{}/i18n/*.po'.format(addon_name)
    pot_filepath = '{addon_name}/i18n/{addon_name}.pot'.format(
        addon_name=addon_name)
    git_export = ''
    if addons_subdirectory:
        po_file_mask = os.path.join(addons_subdirectory, po_file_mask)
        pot_filepath = os.path.join(addons_subdirectory, pot_filepath)
    if git_export_base_url:
        git_export = urljoin(git_export_base_url, 'git/' + project.name)
    tmpl_component = Component.objects.get(slug=tmpl_component_slug)
    addons_to_install = Addon.objects.filter(component=tmpl_component)
    parsed_repository_uri = giturlparse.parse(repository)

    new_component = tmpl_component
    new_component.pk = None
    new_component.project = project
    new_component.name = get_component_name(project, addon_name)
    new_component.slug = get_component_slug(project, addon_name)
    new_component.repo = parsed_repository_uri.url2ssh
    new_component.push = parsed_repository_uri.url2ssh
    new_component.branch = branch
    new_component.filemask = po_file_mask
    new_component.new_base = pot_filepath
    new_component.file_format = 'po'
    new_component.git_export = git_export
    new_component.locked = False
    new_component.save(force_insert=True)

    for addon_to_install in addons_to_install:
        addon_to_install.pk = None
        addon_to_install.component = new_component
        addon_to_install.save()
    return new_component


@click.command()
@click.option(
    '--repository', required=True,
    help="Ssh url to git repository.",
)
@click.option(
    '--branch', required=True,
    help="Target branch."
)
@click.option(
    '--tmpl-component-slug', required=True,
    help="Slug identifier for the template component."
)
@click.option(
    '--addons-subdirectory',
    help="Addons subdirectory, in case addons are not "
         "at the root of the project (eg odoo/addons)."
)
@click.option(
    '--git-export-base-url',
    help="Base Url for 'Exported repository URL' component attribute. "
         "If not provided, the weblate default is used."
)
def main(
        repository, branch, tmpl_component_slug,
        addons_subdirectory=None, git_export_base_url=None):
    """
    This program initializes a weblate project based on a git repository.

    The git repository must contain at least one installable addon
    with a i18n directory containing the .pot file, otherwise it does nothing.
    A first component is created for one of these addons, based on the
    provided component template. Subsequent components can be created
    with wocg-create-components.
    """
    create_project(
        repository, branch, tmpl_component_slug,
        addons_subdirectory=addons_subdirectory,
        git_export_base_url=git_export_base_url)

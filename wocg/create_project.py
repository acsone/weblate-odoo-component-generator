# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import re

import click
import giturlparse

import django
django.setup()  # noqa: E402

from weblate.trans.models import Project, Component

from .tools.component import copy_installed_addons
from .tools.git_utils import temp_git_clone
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


def project_exists(project_name):
    try:
        Project.objects.get(name=project_name)
        return True
    except Project.DoesNotExist:
        return False


def create_project(
        repository, branch, tmpl_component_slug,
        addons_subdirectory=None, use_ssh=False):
    project_name = get_project_name(repository, branch)

    logger.info("Project name is %s", project_name)

    if project_exists(project_name):
        logger.info("Project %s already exists.", project_name)
        return

    with temp_git_clone(repository, branch, use_ssh=use_ssh) as repo_dir:
        addons = get_translatable_addons(
            repo_dir, addons_subdirectory=addons_subdirectory)

        if not addons:
            logger.info("No addons found in %s %s", repository, branch)
            return

        logger.info("Going to create Project %s.", project_name)
        addon_name = next(iter(addons.keys()))
        new_project = get_new_project(
            project_name,
            repository,
            tmpl_component_slug,
        )

        try:
            get_new_component(
                new_project, repository, branch, addon_name,
                tmpl_component_slug,
                addons_subdirectory=addons_subdirectory,
                use_ssh=use_ssh,
            )
        except Exception as e:
            logger.exception(e)
            new_project.delete()


def get_new_project(project_name, repository, tmpl_component_slug):
    tmpl_component = Component.objects.get(slug=tmpl_component_slug)
    new_project = Project()
    new_project.name = project_name
    new_project.slug = get_project_slug(project_name)
    new_project.web = giturlparse.parse(repository).url2https
    new_project.access_control = \
        tmpl_component.project.access_control
    new_project.enable_review = \
        tmpl_component.project.enable_review
    new_project.enable_hooks = \
        tmpl_component.project.enable_hooks
    new_project.set_language_team = \
        tmpl_component.project.set_language_team
    new_project.source_language = \
        tmpl_component.project.source_language
    new_project.instructions = \
        tmpl_component.project.instructions
    new_project.mail = \
        tmpl_component.project.mail
    new_project.save()
    return new_project


def get_new_component(
        project, repository, branch, addon_name, tmpl_component_slug,
        addons_subdirectory=None, use_ssh=False):
    po_file_mask = '{}/i18n/*.po'.format(addon_name)
    pot_filepath = '{addon_name}/i18n/{addon_name}.pot'.format(
        addon_name=addon_name)
    if addons_subdirectory:
        po_file_mask = os.path.join(addons_subdirectory, po_file_mask)
        pot_filepath = os.path.join(addons_subdirectory, pot_filepath)
    tmpl_component = Component.objects.get(slug=tmpl_component_slug)
    tmpl_component_pk = tmpl_component.pk
    parsed_repository_uri = giturlparse.parse(repository)

    repo_url = use_ssh and parsed_repository_uri.url2ssh or repository

    new_component = tmpl_component
    new_component.pk = None
    new_component.project = project
    new_component.name = get_component_name(project, addon_name)
    new_component.slug = get_component_slug(project, addon_name)
    new_component.repo = repo_url
    new_component.push = repo_url
    new_component.branch = branch
    new_component.filemask = po_file_mask
    new_component.new_base = pot_filepath
    new_component.file_format = 'po'
    new_component.locked = False
    new_component.save(force_insert=True)
    copy_installed_addons(tmpl_component_pk, new_component)
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
    '--use-ssh',
    is_flag=True,
    help="Use SSH instead HTTP to clone the repository."
)
def main(
        repository, branch, tmpl_component_slug,
        addons_subdirectory=None, use_ssh=False):
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
        use_ssh=use_ssh,
    )

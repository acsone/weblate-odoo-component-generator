# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

from wocg.tools.git_utils import git_clone
from wocg.tools.helper import get_component_slug, get_component_name
from wocg.tools.manifest import get_translatable_addons

import click
import logging
import os
import re
import django
django.setup()

from weblate.trans.models import Project, Component

_logger = logging.getLogger()


def get_project_name(repository, branch):
    repo_name = repository.split('/')[-1].replace('.git', '')
    sanitized_branch_name = re.sub(r'[.]', '-', branch)
    return '%s-%s' % (repo_name, sanitized_branch_name)


def create_project(
        repository, branch, tmpl_component_slug, addons_sub_directory=None):
    project_name = get_project_name(repository, branch)

    _logger.info("Project name is %s" % project_name)

    try:
        Project.objects.get(name=project_name)
        _logger.info("Project %s already exists." % project_name)
    except Project.DoesNotExist:
        repo_dir = git_clone(repository, branch)
        addons = get_translatable_addons(
            repo_dir, addons_sub_directory=addons_sub_directory)

        if not addons:
            _logger.info("No addons found in %s %s" % (repository, branch))
            return

        _logger.info("Going to create Project %s." % project_name)
        addon_name = addons.keys()[0]
        new_project = get_new_project(project_name, repository)

        try:
            get_new_component(
                new_project, repository, branch, addon_name,
                tmpl_component_slug,
                addons_sub_directory=addons_sub_directory)
        except Exception as e:
            _logger.exception(e)
            new_project.delete()


def get_new_project(project_name, url):
    new_project = Project()
    new_project.name = project_name
    new_project.slug = project_name
    new_project.web = url
    new_project.enable_review = True
    new_project.save()
    return new_project


def get_new_component(
        project, repository, branch, addon_name, tmpl_component_slug,
        addons_sub_directory=None):
    po_file_mask = '{}/i18n/*.po'.format(addon_name)
    pot_filepath = '{addon_name}/i18n/{addon_name}.pot'.format(
        addon_name=addon_name)
    if addons_sub_directory:
        po_file_mask = os.path.join(addons_sub_directory, po_file_mask)
        pot_filepath = os.path.join(addons_sub_directory, pot_filepath)
    tmpl_component = Component.objects.get(slug=tmpl_component_slug)
    new_component = tmpl_component
    new_component.pk = False
    new_component.project = project
    new_component.name = get_component_slug(project, addon_name)
    new_component.slug = get_component_name(project, addon_name)
    new_component.repo = repository
    new_component.push = repository
    new_component.branch = branch
    new_component.filemask = po_file_mask
    new_component.new_base = pot_filepath
    new_component.file_format = 'po'
    new_component.save(force_insert=True)
    return new_component


@click.command()
@click.option('--repository', required=True)
@click.option('--branch', required=True)
@click.option('--tmpl-component-slug', required=True)
@click.option('--addons-sub-directory')
def main(repository, branch, tmpl_component_slug, addons_sub_directory=None):
    """
    This methods should be called to init a project based on a git repository.
    The Git repository should contains at least one installable addons
    with a i18n repository containing the .pot file
    :param repository: SSH URL to repository
    :param branch: target branch
    :param tmpl_component_slug: component slug of the template
    :param addons_sub_directory:
    """
    create_project(
        repository, branch, tmpl_component_slug,
        addons_sub_directory=addons_sub_directory)

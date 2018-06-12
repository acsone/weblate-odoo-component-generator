# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)


def get_component_name(project, addon):
    return "%s-%s" % (project.name, addon)


def get_component_slug(project, addon):
    return "%s-%s" % (project.slug, addon)

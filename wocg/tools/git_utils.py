# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)

import subprocess
import tempfile


def git_clone(repository, branch):
    temp_dir_path = tempfile.mkdtemp()
    subprocess.check_call([
        'git',
        'clone',
        repository,
        '-b', branch,
        temp_dir_path,
    ])
    return temp_dir_path

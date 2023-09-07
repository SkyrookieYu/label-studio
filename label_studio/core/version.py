from __future__ import print_function

"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
""" Version Lib
Copyright (C) 2019 Maxim Tkachenko 

This library automatically generates version of package based on git.
If 'git desc' is successful it will write version to __version__.py:git_version.  
If 'git desc' is fail it will read __version__.py:git_version.

ATTENTION: do not include version_.py to git! It will affect git commit always!
"""
import json
import logging
import os
import sys
from subprocess import STDOUT, CalledProcessError
from subprocess import check_output as run

VERSION_FILE = 'version_.py'
LS_VERSION_FILE = 'ls-version_.py'
VERSION_OVERRIDE = os.getenv('VERSION_OVERRIDE', '')
BRANCH_OVERRIDE = os.getenv('BRANCH_OVERRIDE', '')


def _write_py(info):
    # go to current dir to package __init__.py
    cwd = os.getcwd()
    d = os.path.dirname(__file__)
    d = d if d else '.'
    os.chdir(d)

    info_str = json.dumps(info)

    # write txt
    with open(VERSION_FILE, 'w') as f:
        os.chdir(cwd)  # back current dir
        f.write('info = %s\n' % info_str +
                '\n# This file is automatically generated by version.py'
                '\n# Do not include it to git!\n')


def _read_py(ls=False):
    # go to current dir to package __init__.py
    cwd = os.getcwd()
    d = os.path.dirname(__file__)
    d = d if d else '.'
    sys.path.append(d)
    os.chdir(d)

    # read version
    def import_version_module(file_path):
        try:
            return __import__(os.path.splitext(file_path)[0])
        except ImportError:
            return None

    try:
        version_module = import_version_module(LS_VERSION_FILE if ls else VERSION_FILE)

        if not version_module and ls:
            version_module = import_version_module(VERSION_FILE)

        if version_module:
            return version_module.info
        else:
            return {}
    finally:
        os.chdir(cwd)  # back to current dir


# get commit info: message, date, hash, branch
def get_git_commit_info(skip_os=True, ls=False):

    cwd = os.getcwd()
    d = os.path.dirname(__file__)
    d = d if d else '.'
    os.chdir(d)

    try:
        # take version from git
        try:
            desc = run('git describe --long --tags --always --dirty', stderr=STDOUT, shell=True).decode("utf-8")
            info = {
                'message': run('git show -s --format=%s', stderr=STDOUT, shell=True).strip().decode('utf8'),
                'commit': run('git show -s --format=%H', stderr=STDOUT, shell=True).strip().decode('utf8'),
                'date': run('git log -1 --format="%cd" --date="format:%Y/%m/%d %H:%M:%S"', stderr=STDOUT, shell=True).strip().decode('utf8'),
                'branch': BRANCH_OVERRIDE if BRANCH_OVERRIDE else run("git branch --sort=committerdate -r --contains | grep -m 1 -v HEAD | cut -d'/' -f2-", stderr=STDOUT, shell=True).strip().decode('utf8')
            }
        except CalledProcessError:
            os.chdir(cwd)
            return _read_py(ls=True)

        # create package version
        version = desc.lstrip('v').rstrip().replace('-', '+', 1).replace('-', '.')
        # take OS name
        if not skip_os:
            keys = ('ID=', 'VERSION_ID=', 'RELEASE=')
            with open('/etc/os-release') as f:
                os_version = ''.join(str(s).split("=", 1)[1].rstrip().strip('"').replace('.', '')
                                     for s in f if str(s).startswith(keys))
                version += '.' + os_version
        info['version'] = VERSION_OVERRIDE if VERSION_OVERRIDE else version

        _write_py(info)
        return info

    except Exception as e:
        raise e

    finally:
        os.chdir(cwd)  # back current dir


def get_git_version(skip_os=True):
    info = get_git_commit_info(skip_os)
    return info.get('version', '')


# get only tag from git
def get_short_version():
    version = get_git_version()
    return version.split('+')[0]


if __name__ == '__main__':
    # init version_.py file
    get_git_version()

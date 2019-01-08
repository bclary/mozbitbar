# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function

import json
import os
import string

import mock
import pytest

from mozbitbar import MozbitbarFrameworkException, MozbitbarProjectException
from mozbitbar.bitbar_project import BitbarProject
from testdroid import RequestResponseError
from testdroid import Testdroid as Bitbar


@pytest.fixture
def initialize_project():
    # initialize a dummy project for when the __init__ method is not
    # under test.
    kwargs = {
        'project_name': 'mock_project',
        'TESTDROID_USERNAME': 'MOCK_ENVIRONMENT_VALUE_TEST',
        'TESTDROID_PASSWORD': 'MOCK_ENVIRONMENT_VALUE_TEST',
        'TESTDROID_APIKEY': 'MOCK_ENVIRONMENT_VALUE_TEST',
        'TESTDROID_URL': 'https://www.mock_test_env_var.com',
    }
    return BitbarProject('existing', **kwargs)


# Existing projects #


@pytest.mark.parametrize('kwargs,expected', [
    (
        {'project_id': 11},
        {'id': 11}
    ),
    (
        {'project_id': 99},
        {'id': 99}
    ),
    ({'project_id': 100}, MozbitbarProjectException),
    ({'project_id': 2**32}, MozbitbarProjectException),
    ({'project_id': -1}, MozbitbarProjectException),
    (
        {'project_name': 'mock_project'},
        {'name': 'mock_project', 'id': 1}
    ),
    (
        {'project_name': 'another_mock_project'},
        {'name': 'another_mock_project', 'id': 99}
    ),
    ({'project_name': string.lowercase}, MozbitbarProjectException),
    ({'project_name': 'NULL'}, MozbitbarProjectException),
    ({'project_name': 'None'}, MozbitbarProjectException),
    (
        {'project_id': 11, 'project_name': 'mock_project'},
        {'id': 11, 'name': 'mock_project'}
    ),
    (
        {'project_id': 10000, 'project_name': 'mock_project'},
        {'id': 10000, 'name': 'yet_another_mock_project'}
    )

])
def test_bb_project_init_existing(kwargs, expected):
    """Ensures BitbarProject is able to retrieve existing project by id
    or name, and process resulting output of the (mocked) call.

    Directly tests methods involved in:
        - initialization of project
        - retrieve and set project parameters by id or name
    """
    if expected is MozbitbarProjectException:
        with pytest.raises(MozbitbarProjectException):
            BitbarProject('existing', **kwargs)

    else:
        project = BitbarProject('existing', **kwargs)
        assert (
            project.project_id == expected.get('id') or
            project.project_name == expected.get('name')
        )

# Project status #


@pytest.mark.parametrize('project_status,expected', [
    ('present', MozbitbarProjectException),
    ('exist', MozbitbarProjectException),
    ('create', MozbitbarProjectException),
])
def test_bb_project_status(project_status, expected):
    """Ensures BitbarProject raises an exception on invalid project status.
    """
    if expected is MozbitbarProjectException:
        with pytest.raises(MozbitbarProjectException):
            BitbarProject(project_status)


# Create project #


@pytest.mark.parametrize('kwargs,expected', [
    (
        {
            'project_name': 'parametrized_project',
            'project_type': 'parametrized_type'
        },
        {
            'project_name': 'parametrized_project',
            'project_type': 'parametrized_type'
        },
    ),
    (
        {
            'project_name': string.punctuation,
            'project_type': string.lowercase
        },
        {
            'project_name': string.punctuation,
            'project_type': string.lowercase
        }
    ),
    (
        {
            'project_name': 'mock_project',
            'project_type': 'mock_type'
        },
        MozbitbarProjectException
    ),
    (
        {
            'project_name': 'mock_project',
            'project_type': 'mock_type',
            'permit_duplicate': True
        },
        {
            'project_name': 'mock_project',
            'project_type': 'mock_type'
        }
    )
])
def test_bb_project_init_create_new_project(kwargs, expected):
    """Ensures BitbarProject.create_project() is able to create a project if
    the name is unique. Otherwise, the default behavior is raise an exception,
    unless the permit_duplicate flag is set.
    """
    if expected is MozbitbarProjectException:
        with pytest.raises(MozbitbarProjectException):
            project = BitbarProject('new', **kwargs)
    else:
        project = BitbarProject('new', **kwargs)
        assert project.project_id is not None
        assert project.project_name == expected['project_name']
        assert project.project_type == expected['project_type']


def test_bb_project_create(initialize_project):
    kwargs = {
        'project_name': 'mock_test',
        'project_type': 'mock_type'
    }
    with pytest.raises(MozbitbarProjectException):
        with mock.patch.object(Bitbar,
                               'create_project',
                               side_effect=RequestResponseError(
                                    msg='mock_error', status_code=400)):
            initialize_project.create_project(**kwargs)


# Project Framework #


@pytest.mark.parametrize('kwargs,expected', [
    (
        {'framework_id': -1},
        MozbitbarFrameworkException
    ),
    (
        {'framework_id': 1},
        {'framework_name': 'mock_framework', 'framework_id': 1}
    ),
    (
        {'framework_name': 'mock_framework'},
        {'framework_name': 'mock_framework', 'framework_id': 1}
    ),
    (
        {'framework_name': 'mock_framework', 'framework_id': 1},
        {'framework_name': 'mock_framework', 'framework_id': 1}
    ),
    ({'framework_name': u'mock_framework', 'framework_id': 1}, {
     'framework_name': 'mock_framework', 'framework_id': 1}),
    ({'framework_name': 'mock_unicode_framework'},
     {'framework_name': 'mock_unicode_framework', 'framework_id': 2}),
])
def test_bb_project_framework(initialize_project, kwargs, expected):
    if expected is MozbitbarFrameworkException:
        with pytest.raises(MozbitbarFrameworkException):
            initialize_project.set_project_framework(**kwargs)
    else:
        initialize_project.set_project_framework(**kwargs)
        assert initialize_project.framework_id == expected['framework_id']
        assert initialize_project.framework_name == expected['framework_name']


# Project config #


@pytest.mark.parametrize('kwargs,expected', [
    (
        {'timeout': 10},
        {'timeout': 10}
    ),
    (
        {'timeout': 10, 'scheduler': 'SINGLE'},
        {'timeout': 10, 'scheduler': 'SINGLE'}
    ),
    (
        'not_a_dict', TypeError
    ),
    (
        {'scheduler': 'SINGLE'},
        None
    )
])
def test_set_project_config_new_config(initialize_project, kwargs, expected):
    if expected is TypeError:
        with pytest.raises(TypeError):
            initialize_project.set_project_configs(new_config=kwargs)
    else:
        initialize_project.set_project_configs(new_config=kwargs)


@pytest.mark.parametrize('kwargs,expected', [
    (
        {'path': 'mock_config.json', 'config': {'mock': True}},
        {'mock': True}
    ),
    (
        {'config': {"scheduler": "SINGLE", "timeout": 0}},
        {"scheduler": "SINGLE", "timeout": 0}
    )
])
def test_load_project_config(initialize_project, kwargs, expected):
    # if kwargs['path'] is defined, it is a temporary file
    if kwargs.get('path'):
        with open(kwargs.get('path'), 'w') as temporary_file:
            json.dump(kwargs.get('config'), temporary_file)

    # this method does its own assertions
    initialize_project.set_project_configs(path=kwargs.get('path'))

    # clean up temporary file
    if kwargs.get('path'):
        os.remove(kwargs.get('path'))


# Other methods #

def test_get_user_id(initialize_project):
    output = initialize_project.get_user_id()
    assert output
    assert type(output) == int
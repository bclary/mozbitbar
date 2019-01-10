# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function

import json
import logging
import os
import time

from mozbitbar import (MozbitbarDeviceException, MozbitbarFileException,
                       MozbitbarFrameworkException, MozbitbarProjectException,
                       MozbitbarTestRunException)
from mozbitbar.configuration import Configuration
from testdroid import RequestResponseError

logger = logging.getLogger('mozbitbar')


class BitbarProject(Configuration):
    """BitbarProject is a class which represents an instance of a project on
    Bitbar, as well as associated actions that are intended to be run against
    a specific project instance.

    This class holds attributes that are not tracked in the Testdroid
    implementation relating to the project, device groups and/or test runs.
    """
    def __init__(self, project_status, **kwargs):
        """Initializes the BitbarProject class instance.

        Two methods of are currently supported:
            - new project ('new')
            - use of existing project ('existing')

        If a new project is specified, project_type and project_name attributes
        must be provided.

        If an existing project is specified, at minimum the project_name or
        project_id must be specified.

        Args:
            project_status (str): Expected to be 'new' or 'existing'.
                Raises an exception on any other input.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            MozbitbarProjectException: If project_status has value other
                than 'new' or 'existing'.
        """
        credentials = {key: value for (key, value) in kwargs.iteritems()
                       if 'TESTDROID' in key}

        super(BitbarProject, self).__init__(**credentials)

        new_kwargs = dict(set(kwargs.items()) ^ set(credentials.items()))

        if 'new' in project_status:
            logger.debug('Create new project')
            self.create_project(**new_kwargs)
        elif 'existing' in project_status:
            logger.debug('Use existing project')
            self.use_existing_project(**new_kwargs)
        else:
            msg = 'Invalid project status: {}'.format(project_status)
            raise MozbitbarProjectException(message=msg)

    # Class attributes #

    @property
    def project_id(self):
        """Returns the project_id attribute.

        When setting the project_id, checks are performed to ensure the value
        is an integer.

        Args:
            project_id (int): Value to set for the project_id attribute
                of this object.

        Raises:
            ValueError: If project_id is not of type int.
        """
        return self.__project_id

    @project_id.setter
    def project_id(self, project_id):
        if type(project_id) is not int:
            raise ValueError('{}: invalid project_id type: '.format(__name__) +
                             'expected int, received {}'.format(
                                 type(project_id)))
        self.__project_id = project_id

    @property
    def project_name(self):
        """Returns the project_name attribute.

        Args:
            project_name (str): Value to set for the project_name attribute
                of this object.
        """
        return self.__project_name

    @project_name.setter
    def project_name(self, project_name):
        self.__project_name = project_name

    @property
    def project_type(self):
        """Returns the project_type attribute.

        Args:
            project_type (str): Value to set for the project_type attribute
                of this object.
        """
        return self.__project_type

    @project_type.setter
    def project_type(self, project_type):
        self.__project_type = project_type

    @property
    def device_group_id(self):
        """Returns the device_group_id attribute.

        Args:
            device_group_id (int): Value to set for the device_group_id
            attribute of this object.

        Raises:
            ValueError: If device_group_id is not of type int.
        """
        return self.__device_group_id

    @device_group_id.setter
    def device_group_id(self, device_group_id):
        self.__device_group_id = int(device_group_id)

    @property
    def device_group_name(self):
        """Returns the device_group_name attribute.

        Args:
            device_group_name (str): Value to set for the device_group_name
            attribute of this object.

        Raises:
            ValueError: If device_group_name is not of type str.
        """
        return self.__device_group_name

    @device_group_name.setter
    def device_group_name(self, device_group_name):
        self.__device_group_name = str(device_group_name)

    @property
    def framework_id(self):
        """Returns the framework_id attribute.

        Args:
            framework_id (int): Value to set for the framework_id attribute
                of this object.
        """
        return self.__framework_id

    @framework_id.setter
    def framework_id(self, framework_id):
        self.__framework_id = int(framework_id)

    @property
    def framework_name(self):
        """Returns the framework_name attribute.

        Args:
            framework_name (str): Value to set for the framework_name attribute
                of this object.
        """
        return self.__framework_name

    @framework_name.setter
    def framework_name(self, framework_name):
        self.__framework_name = str(framework_name)

    @property
    def device_id(self):
        """Returns the device_id attribute.

        Args:
            id (int): Value to set for the device_group_id attribute of this
                object.

        Returns:
            int: Value set for the device_id attribute of this object.
        """
        return self.__device_id

    @device_id.setter
    def device_id(self, id):
        self.__device_id = int(id)

    # Additional Methods #

    def _set_project_attributes(self, response):
        """Sets class attributes from the parameter value.

        Args:
            response (:obj:`dict`): Response from Bitbar represented as
                dictionary of strings.
        """
        self.project_id = response['id']
        self.project_name = response['name']
        self.project_type = response['type']

    def get_user_id(self):
        """Retrieves the user id for the currently authenticated user.

        This method is a wrapper around the Testdroid implementation.

        Returns:
            int: currently authenticated user id.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        return self.client.get_me()['id']

    def _file_on_local_disk(self, path):
        """Checks if specified path can be found on local disk.

        Accepts a string representation of a local path, which is turned into
        an absolute path. Then the location specified by the path is checked
        using the os module.

        Args:
            path (str): String representation of a path on local disk.

        Returns:
            bool: True if path is found on local disk. False otherwise.
        """
        path = str(path)
        logger.debug(' '.join(['Absolute path:', os.path.abspath(path)]))
        return os.path.isfile(os.path.abspath(path))

    def _open_file(self, path):
        """Given a path, opens the file and reads its contents.

        Args:
            path (str): String representation of a path on local disk.

        Returns:
            str: String representation of the contents of the file.

        Raises:
            MozbitbarFileException: If path does not map to an existing file.
        """
        if self._file_on_local_disk(path):
            with open(path, 'r') as f:
                return f.read()

        msg = 'File could not be located for opening'
        logger.critical(msg)
        raise MozbitbarFileException(message=msg, path=path)

    # Project operations #

    def get_projects(self):
        """Returns the list of projects.

        Returns:
            dict: Contains data on projects available on Bitbar.
        """
        existing_projects = self.client.get_projects()
        return existing_projects['data']

    def create_project(self, project_name, project_type,
                       permit_duplicate=False):
        """Creates a new Bitbar project using provided parameters.

        By default, Mozilla does not permit multiple projects with same name
        on Bitbar. This behavior can be overridden using the permit_duplicate
        parameter.

        If project creation is successful, relevant attributes of the new
        project is stored as object attributes.

        Args:
            project_name (str): Project name to be assigned to new project.
            project_type (str): Project type to be assigned to new project
            permit_duplicate (bool, optional): If True, permit creation of
                project even if the provided name already exists on Bitbar.

        Raises:
            MozbitbarProjectException: If permit_duplicate is False and
                project with same name already exists on Bitbar.
        """
        if not permit_duplicate:
            existing_projects = self.get_projects()
            if any([project['name'] == project_name
                   for project in existing_projects]):
                msg = '{}: project_name: {} already exists'.format(
                    __name__,
                    project_name
                )
                raise MozbitbarProjectException(message=msg)

        # TODO: check if project_type specified is valid.

        try:
            output = self.client.create_project(project_name, project_type)
        except RequestResponseError as rre:
            raise MozbitbarProjectException(message=rre.args,
                                            status_code=rre.status_code)

        self._set_project_attributes(output)

    def use_existing_project(self, project_id=None, project_name=None):
        """Retrieve existing Bitbar project details.

        Acceptable project identifiers are either one of project_name or
        project_id. If both are provided, the id is prioritized due to its
        guaranteed uniqueness.

        Args:
            id (int): Integer ID of the project.
            name (str): String representation of the project name.

        Raises:
            MozbitbarProjectException: If neither project_id nor
                project_name map to an existing project on Bitbar.
        """
        available_projects = self.get_projects()
        for project in available_projects:
            if (project_id and project_name is None or
                    project_id and project_name):
                if project_id is project['id']:
                    project_name = project['name']
                    break

            elif project_name and project_id is None:
                if project_name is project['name']:
                    project_id = project['id']
                    break

        if (project_id and project_name) is None:
            msg = '{}: project_name: {}, project_id: {} '.format(
                __name__,
                project_name,
                project_id
            ) + 'not found on Bitbar'
            raise MozbitbarProjectException(message=msg)

        self._set_project_attributes(project)

    def get_project_configs(self):
        return self.client.get_project_config(self.project_id)

    def set_project_configs(self, new_values=None, path=None):
        """Overwrites part or all of project configuration with new values.

        Provided with either a dict of config values or path to a json file
        containing configs, this method will load the values, filter out
        values that would be unchanged, then make calls to Bitbar in order
        to write the configuration values.

        Args:
            new_values (:obj:`dict`, optional): Project configuration
                represented as dict.
            path (str, optional): Path to a locally stored file containing
                project configuration.

        Return:
            None: When no actions need to be performed.

        Raises:
            MozbitbarProjectException: If new_config is not a valid dict.
        """
        if not new_values and not path:
            msg = 'Neither new config values or path to config file has \
                   been set.'
            raise MozbitbarProjectException(message=msg)

        if new_values and not path:
            logger.debug('New config provided as parameter.')

        if path and not new_values:
            if not self._file_on_local_disk(path):
                msg = 'Specified path not found on disk: {}'.format(path)
                logger.error(msg)
                return

            new_values = self._load_project_config(os.path.abspath(path))

        existing_configs = self.get_project_configs()

        for key in list(new_values.keys()):
            if new_values.get(key) == existing_configs.get(key):
                new_values.pop(key)

        if len(new_values) is 0:
            msg = 'No project configuration values need to be updated'
            logger.info(msg)
            return

        try:
            self.client.set_project_config(self.project_id, **new_values)
        except RequestResponseError as rre:
            raise MozbitbarProjectException(message=rre.args,
                                            status_code=rre.status_code)
        except ValueError as ve:
            raise MozbitbarProjectException(message=ve.args)

    def _load_project_config(self, path='project_config.json'):
        """Loads project config from the disk.

        Args:
            path (str): Path to the configuration file on local disk.

        Returns:
            dict: JSON-parsed configuration.

        Raises:
            MozbitbarFileException: If path to file is not found.
            TypeError: If opened file did not contain JSON-formatted content.
        """
        opened_file = json.loads(self._open_file(path))
        if type(opened_file) is not dict:
            msg = 'Loaded config is not a valid dict'
            raise TypeError(msg)

        return opened_file

    def set_project_framework(self, framework_name=None, framework_id=None):
        """Sets the project framework using either integer id or name.

        This method prioritizes the usage of framework name if both id and
        name are provided, but do not belong to the same framework on Bitbar.

        If framework id or name provided is not available on Bitbar, a
        MozbitbarFrameworkException is raised.

        Args:
            framework_name (str): String representation of the framework name.
            framework_id (int): Integer ID of the framework.

        Raises:
            MozbitbarFrameworkException: If framework name or framework id
                provided does not match any existing frameworks on Bitbar.
            RequestResponseError: If Testdroid responds with an error.
        """
        # looks redundant, except Python 2 has strings and then Unicode strings
        if framework_id:
            framework_id = int(framework_id)
        if framework_name:
            framework_name = str(framework_name)

        available_frameworks = self.get_project_frameworks()

        for framework in available_frameworks:
            if framework.get('name') == framework_name:
                framework_id = framework.get('id')
                break
            elif framework.get('id') == framework_id:
                framework_name = framework.get('name')
                break

        if not (framework_id and framework_name):
            msg = 'Framework ID and/or name was invalid.'
            raise MozbitbarFrameworkException(message=msg)

        self.client.set_project_framework(self.project_id, framework_id)

        self.framework_id = framework_id
        self.framework_name = framework_name

    def get_project_frameworks(self):
        """Returns list of project frameworks available to the user.

        Returns:
            :obj:`dict` of :obj:`str`
        """
        output = self.client.get_frameworks()
        return output['data']

    def set_project_parameters(self, parameters, force_overwrite=False):
        """Sets project parameters.

        Will accept any number of parameters in the form of a list.

        If specified parameter is already set, the default behavior is to
        retain existing parameter, moving to the next specified parameter.

        If the force_overwrite flag is supplied, all existing parameters
        that match list of supplied parameters are first removed from
        the project. The parameters are then set from the list of supplied
        parameters as normal, in effect overwriting the parameter values.

        Args:
            parameters (:obj:`list` of :obj:`dict`): List of project parameters
                to be set for the current project.
            force_overwrite (bool, optional): True if project parameters are
                to be overwritten. False by default.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        if not parameters:
            logger.info('No project parameters supplied.')
            return

        if force_overwrite:
            for parameter in parameters:
                # delete existing project parameters that match the key values
                # in 'parameters' argument.
                self.delete_project_parameter(parameter['key'])

        for parameter in parameters:
            try:
                self.client.set_project_parameters(self.project_id,
                                                   parameter)
            except RequestResponseError as rre:
                if rre.status_code == 409:
                    # not an error per se, just means there exists already a
                    # parameter with the given key name.
                    logger.info(', '.join([''.join(rre.args), 'skipping..']))
                else:
                    logger.critical('Testdroid responded with an error')
                    raise MozbitbarProjectException(message=rre.args,
                                                    status_code=rre.status_code)

    def delete_project_parameter(self, parameter_to_delete):
        """Deletes a single project parameter from the project.

        Given a single instance of a project parameter, this method will
        attempt to delete the project parameter from the project.

        Accepts both integer and string representation of the parameter id
        and name, respectively.

        If the parameter to delete is found, an attempt is made using
        Testdroid to delete the said parameter.

        Args:
            parameter_to_delete (str, int): Project parameter to be deleted
                from the project. Could be string (name) or integer (id).

        Raises:
            MozbitbarProjectException: If HTTPS response of the deletion
                attempt returns anything other than 204.
        """
        try:
            # maybe user supplied a stringified integer value.
            sanitized_parameter_id = int(parameter_to_delete)
        except ValueError:
            # if not, we have a parameter_name that needs conversion to id.
            sanitized_parameter_id = self.get_project_parameter_id(
                parameter_to_delete)

        if sanitized_parameter_id is None:
            # if user-supplied parameter name or id is not in fact set for the
            # project on Bitbar, skip the deletion process.
            msg = ', '.join([
                'Parameter: {} is not set for project'.format(
                    parameter_to_delete),
                'skipping deletion'
            ])
            logger.info(msg)
            return

        self.client.delete_project_parameters(
            self.project_id,
            sanitized_parameter_id
        )

    def get_project_parameter_id(self, parameter_name):
        """Returns the parameter_id value.

        This method will convert the string representation of the
        project parameter name to an integer id.

        Args:
            parameter_name (str): Parameter name in string format, to convert
                to a numerical ID.

        Returns:
            int or None: Integer if parameter name maps to an existing project
                parameter on Bitbar. None otherwise.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        output = self.client.get_project_parameters(self.project_id)
        for parameter in output['data']:
            if parameter_name == parameter['key']:
                return parameter['id']

        return None

    # File operations #

    def _file_on_bitbar(self, filename):
        """Checks if file with same name has been uploaded to Bitbar which
        is available to the user.

        Args:
            filename (str): String representation of a filename.

        Returns:
            bool: True if filename is found on Bitbar. False otherwise.
        """
        # sanitize the provided path to just the file name itself.
        filename = os.path.basename(str(filename))

        output = self.client.get_input_files()
        return any([file_list['name'] == filename
                   for file_list in output['data']])

    def upload_file(self, **kwargs):
        """Uploads file(s) to Bitbar.

        Supports upload of multiple files, of all types supported by Bitbar.

        Args:
            files (:obj:`dict`): Dictionary of key/value pairs containing the
                file type and path.

        Raises:
            MozbitbarFileException: If file type is unsupported, or file
                specified could not be found on disk, or file failed to upload
                to Bitbar.
        """
        for key, filename in kwargs.iteritems():
            file_type, _ = key.split('_')

            if file_type not in ['application', 'test', 'data']:
                msg = 'Unsupported file type: {}'.format(file_type)
                raise MozbitbarFileException(message=msg)

            if not self._file_on_local_disk(filename):
                msg = 'Failed to locate on disk: {}'.format(filename)
                raise MozbitbarFileException(path=filename, message=msg)

            if self._file_on_bitbar(filename):
                # skip and go to the next item in the list of files.
                msg = ', '.join([
                    'File: {} already exists on Bitbar'.format(filename),
                    'skipping upload'
                ])
                logger.info(msg)
                continue

            api_path_components = [
                "users/{user_id}/".format(user_id=self.get_user_id()),
                "projects/{project_id}/".format(project_id=self.project_id),
                "files/{file_type}".format(file_type=file_type)
            ]
            api_path = ''.join(api_path_components)

            try:
                self.client.upload(path=api_path, filename=filename)
            except RequestResponseError as rre:
                raise MozbitbarFileException(message=rre.args,
                                             status_code=rre.status_code)

    # Device operations #

    def get_device_groups(self):
        """Returns the list of device groups available on Bitbar.

        Returns:
            :obj:`list` of :obj:`dict`: List of currently available device
                groups.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        return self.client.get_device_groups()['data']

    def get_devices(self):
        """Returns the list of devices available on Bitbar.

        Returns:
            :obj:`list` of :obj:`dict`: List of currently available devices.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        return self.client.get_devices()['data']

    def set_device_group(self, device_group_name=None, device_group_id=None):
        """Sets the project's device group to be used for test runs.

        Supports referencing device groups by both name and id. This method
        will attempt to find a match for whichever parameter that is supplied.

        Args:
            name (str, optional): Device group name in string.
            id (int, optional): Device group id in integer.

        Raises:
            MozbitbarDeviceException: If neither id nor name was supplied.
        """
        if not device_group_id and not device_group_name:
            msg = 'Neither device_group_name or device_group_id has been \
                   provided.'
            raise MozbitbarDeviceException(message=msg)

        for device_group in self.get_device_groups():
            # fill out missing parameter so we have both id and name.
            if device_group['displayName'] == device_group_name:
                self.device_group_id = device_group['id']
                self.device_group_name = device_group_name
                return
            elif device_group['id'] == device_group_id:
                self.device_group_id = device_group_id
                self.device_group_name = device_group['displayName']
                return
            else:
                continue

        # only incorrect recipes and/or device name/id mismatch leads here.
        msg = 'Supplied device_group_name or device_group_id \
                did not match any device group on Bitbar.'
        raise MozbitbarDeviceException(message=msg)

    def set_device(self, device_id=None, device_name=None):
        """Sets the device using the device_id.

        Accepts either a device name or device id.

        Args:
            device_id (int, str): Device specifier to be used to set the
                device_id attribute. Could be the device name (str) or
                device id (int).

        Raises:
            MozbitbarDeviceException: If device_id is not found in list of
                available device on Bitbar.
        """
        if not device_id and not device_name:
            msg = 'Neither device_name or device_id has been provided.'
            raise MozbitbarDeviceException(message=msg)

        for device in self.get_devices():
            if device['id'] == device_id:
                self.device_id = device_id
                self.device_name = device['displayName']
                return
            elif device['displayName'] == device_name:
                self.device_id = device['id']
                self.device_name = device_id
                return
            else:
                continue

        msg = 'Device specifier not found on Bitbar: {}'.format(device_id)
        raise MozbitbarDeviceException(message=msg)

    # Test Run operations #

    def _is_test_name_unique(self, test_run_name):
        """Cross-checks provided test_run_name against all test run names.

        Args:
            test_run_name (str): Test run name to be compared against all
                previous test runs' names.

        Returns:
            bool: True if test name is unique. False otherwise.
            None: If test_run_name to be checked is None.
        """
        if test_run_name is not None:
            return test_run_name not in [run['displayName']
                                         for run in self.get_all_test_runs()]
        return None

    def start_test_run(self, **kwargs):
        """Starts a test run with parameters provided from the recipe.

        This method is a wrapper around the Testdroid implementation with
        additional operations. Parameters to this method should mirror that of
        the Testdroid implementation.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Raises:
            RequestResponseError: If Testdroid responds with an error.
        """
        # ensure name is unique
        if not kwargs.get('name'):
            msg = 'Test name is not defined.'
            raise MozbitbarTestRunException(message=msg)
        if not self._is_test_name_unique(kwargs.get('name')):
            msg = 'Test name is not unique.'
            raise MozbitbarTestRunException(
                message=msg,
                test_run_name=kwargs.get('name')
            )

        # ensure project ID is set
        if not hasattr(self, 'project_id'):
            msg = 'Project ID is not set.'
            raise MozbitbarProjectException(message=msg)

        # ensure at least one of device_id or device_group_id is set
        if hasattr(self, 'device_group_id'):
            kwargs['device_group_id'] = self.device_group_id
        elif hasattr(self, 'device_id'):
            kwargs['device_model_ids'] = self.device_id
        else:
            msg = 'Device or device group id is not set.'
            raise MozbitbarDeviceException(message=msg)

        self.test_run_id = self.client.start_test_run(self.project_id,
                                                      **kwargs)
        self.test_run_name = kwargs.get('name')

    def configure_and_start_test_run(self, **kwargs):
        if not hasattr(self, 'project_id'):
            msg = 'Project ID is not set.'
            raise MozbitbarProjectException(message=msg)
        pass

    def get_test_run(self, test_run_id=None, test_run_name=None):
        """Returns the test run details.

        Provided with integer value for test_run_id, if the test_run exists
        details for the test run is returned, including the current state
        and success status.

        Same process is done if test_run_name is supplied, except that
        a conversion from the test_run_name to test_run_id occurs as first
        step.

        Args:
            test_run_id (int): ID of the test run.
            test_run_name (str): Name of the test run.

        Returns:
            :obj:`dict` of str: Dictionary of strings containing test run
                information.

        Raises:
            MozbitbarTestRunException: If Testdroid responds with an error.
        """
        if test_run_name:
            test_runs = self.client.get_project_test_runs(self.project_id)
            for test_run in test_runs['data']:
                if test_run_name in test_run.values():
                    test_run_id = test_run['id']
                    break

        if not test_run_id or type(test_run_id) is not int:
            msg = 'Test Run ID is not integer.'
            raise MozbitbarTestRunException(message=msg)

        try:
            output = self.client.get_test_run(self.project_id, test_run_id)
        except RequestResponseError as rre:
            raise MozbitbarTestRunException(message=rre.args,
                                            status_code=rre.status_code)

        return output

    def get_all_test_runs(self):
        """Returns all tests for the project.

        Returns:
            :obj:`dict` of str: Dictionary of strings holding all test run
                information for the project.
        """
        return self.client.get_project_test_runs(self.project_id)['data']

    def notify_test_run_complete(self, interval=30, timeout=300):
        """Waits for test run to complete and outputs status to the CLI.

        Args:
            interval (int, optional): Interval at which this method should
                query Bitbar for status updates for the test run.
            timeout (int, optional): Maximum time to wait before exiting the
                method.
        """
        total_wait_time = 0

        while (total_wait_time <= timeout):
            state = str(self.get_test_run(self.test_run_id)['state'])
            if state != 'FINISHED':
                time.sleep(interval)
                total_wait_time += interval
                logger.debug('Checking test run state for {}...'.format(
                    self.test_run_name))
                logger.debug('Waited {}s...'.format(total_wait_time))
            else:
                break

        test_run_details = self.get_test_run(self.test_run_id)

        if total_wait_time >= timeout:
            msg = 'Test run did not complete prior to {}s timeout.'.format(
                timeout)
            logger.warning(msg)
        logger.info('Project Name: {}'.format(self.project_name))
        logger.info('Project Framework Name: {}'.format(self.framework_name))
        logger.info('Device Group Name: {}'.format(self.device_group_name))
        logger.info('Test Run Name: {}'.format(self.test_run_name))
        logger.info('Test Run State: {}'.format(test_run_details['state']))

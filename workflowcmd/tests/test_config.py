########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import os

import yaml
from path import path
from mock import patch

from workflowcmd import config
from workflowcmd import tests
from workflowcmd.tests import resources


class TestLoader(tests.BaseTest):

    relative_config_path = path('configs') / 'config1.yaml'
    full_config_path = resources.DIR / relative_config_path

    def test_properties(self):
        loader = self._init_loader()
        config1 = yaml.safe_load(self.full_config_path.text())
        expected_blueprint_path = (self.full_config_path.dirname() /
                                   config1['blueprint_path'])
        expected_blueprint_dir = expected_blueprint_path.dirname()
        self.assertEqual(loader.config, config1)
        self.assertEqual(loader.blueprint_path, expected_blueprint_path)
        self.assertEqual(loader.blueprint_dir, expected_blueprint_dir)
        self.assertIsNone(loader.storage_dir)

    def test_parse_parameters(self):
        loader = self._init_loader()
        args = {'arg1': 'arg1_value'}
        with patch.dict(os.environ, {'MY_ENV_VAR': 'MY_ENV_VAR_VALUE'}):
            parsed_params = loader._parse_parameters({
                'arg_based_param': {'arg': 'arg1'},
                'env_based_param': {'env': 'MY_ENV_VAR'},
                'loader_based_param': {'loader': 'config'},
                'concat_based_param': {'concat': ['a', 'b', 'c']}
            }, args=args)
        self.assertEqual(parsed_params, {
            'arg_based_param': 'arg1_value',
            'env_based_param': 'MY_ENV_VAR_VALUE',
            'loader_based_param': loader.config,
            'concat_based_param': 'abc'
        })

    def _init_loader(self):
        return config.Loader(package=resources,
                             config_path=self.relative_config_path)


class TestWorkflowConfPath(tests.BaseTest):

    def test_default_workflowcmd_conf_path(self):
        del os.environ[config.WORKFLOWCMD_CONF_PATH]
        self.assertEqual(config._workflowcmd_conf_path(),
                         os.path.expanduser('~/.workflowcmd'))

    def test_custom_workflowcmd_conf_path(self):
        custom_path = '~/custom'
        with patch.dict(os.environ,
                        {config.WORKFLOWCMD_CONF_PATH: '~/custom'}):
            self.assertEqual(config._workflowcmd_conf_path(),
                             os.path.expanduser(custom_path))

    def test_read_workflowcmd_conf(self):
        mock_data = {'some': 'mock_data'}
        self.workflowcmd_conf_path.write_text(yaml.safe_dump(mock_data))
        self.assertEqual(mock_data, config._read_workflowcmd_conf())

    def test_read_workflowcmd_conf_not_exists(self):
        self.assertFalse(self.workflowcmd_conf_path.exists())
        self.assertEqual({}, config._read_workflowcmd_conf())

    def test_update_workflowcmd_conf_empty(self):
        mock_data = {'some': 'other_mock_data'}
        config._update_workflowcmd_conf(mock_data)
        self.assertEqual(yaml.safe_load(self.workflowcmd_conf_path.text()),
                         mock_data)
        return mock_data

    def test_update_workflowcmd_conf_not_empty(self):
        current = self.test_update_workflowcmd_conf_empty()
        new_mock_data = {'more': 'mocking data'}
        new_mock_data_copy = new_mock_data.copy()
        config._update_workflowcmd_conf(new_mock_data)
        self.assertEqual(new_mock_data, new_mock_data_copy)
        current.update(new_mock_data)
        self.assertEqual(yaml.safe_load(self.workflowcmd_conf_path.text()),
                         current)

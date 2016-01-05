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

from path import path
from mock import patch

from workflowcmd import functions
from workflowcmd import loader
from workflowcmd import tests
from workflowcmd.tests import resources


class TestFunctions(tests.BaseTest):

    relative_config_path = path('configs') / 'plain.yaml'
    full_config_path = resources.DIR / relative_config_path

    def test_parse_parameters(self):
        loader = self._init_loader()
        args = {'arg1': 'arg1_value'}
        with patch.dict(os.environ, {'MY_ENV_VAR': 'MY_ENV_VAR_VALUE'}):
            parsed_params = functions.parse_parameters(loader, {
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
        return loader.Loader(package=resources,
                             config_path=self.relative_config_path)

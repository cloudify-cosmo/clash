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

from mock import patch

from workflowcmd import functions
from workflowcmd import loader as _loader
from workflowcmd import tests
from workflowcmd.tests import resources


class TestFunctions(tests.BaseTest):

    def test_parse_parameters(self):
        full_config_path = resources.DIR / 'configs' / 'plain.yaml'
        loader = _loader.Loader(config_path=full_config_path)
        args = {'arg1': 'arg1_value'}
        with patch.dict(os.environ, {'MY_ENV_VAR': 'MY_ENV_VAR_VALUE'}):
            parsed_params = functions.parse_parameters(loader, {
                'arg_based_param': {'arg': 'arg1'},
                'env_based_param1': {'env': 'MY_ENV_VAR'},
                'env_based_param2': {'env': ['MY_ENV_VAR', 'not in use']},
                'env_based_param3': {'env': ['NON_EXISTENT_ENV', 'fallback']},
                'loader_based_param': {'loader': 'config'},
                'concat_based_param': {'concat': ['a', 'b', 'c']}
            }, args=args)
        self.assertEqual(parsed_params, {
            'arg_based_param': 'arg1_value',
            'env_based_param1': 'MY_ENV_VAR_VALUE',
            'env_based_param2': 'MY_ENV_VAR_VALUE',
            'env_based_param3': 'fallback',
            'loader_based_param': loader.config,
            'concat_based_param': 'abc'
        })

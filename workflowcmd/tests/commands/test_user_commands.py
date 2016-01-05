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

import json

from workflowcmd import tests


class TestUserCommands(tests.BaseTest):

    def test_basic_command(self):
        self._test_command(verbose=False, command=['command1'])

    def test_verbose_basic_command(self):
        self._test_command(verbose=True, command=['command1'])

    def test_nested_command(self):
        self._test_command(verbose=False, command=['nested', 'command2'])

    def _test_command(self, verbose, command):
        config_path = 'end_to_end.yaml'
        output_path = self.workdir / 'output.json'
        self.dispatch(config_path, 'setup')
        self.dispatch(config_path, 'init')
        args = [config_path] + command + ['arg1_value']
        output = self.dispatch(*args, a='arg3_value', output_path=output_path,
                               verbose=verbose).stdout
        self.assertEqual(json.loads(output_path.text()), {
            'param1': 'arg1_value',
            'param2': 'arg2_default',
            'param3': 'arg3_value'
        })
        self.assertIn('from workflow1', output)
        assertion = self.assertIn if verbose else self.assertNotIn
        assertion("Starting 'workflow1'", output)

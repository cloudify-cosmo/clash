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

import sh

from workflowcmd import tests


class TestInit(tests.BaseTest):

    INPUT = 'INPUT_VALUE'

    def test_basic(self, setup=True, reset=False, config_path='basic.yaml'):
        if setup:
            self.dispatch(config_path, 'setup')
            inputs = self.inputs(config_path)
            inputs['input'] = self.INPUT
            self.set_inputs(config_path, inputs)
        self.dispatch(config_path, 'init', reset=reset)
        env = self.env(config_path)
        instances = env.storage.get_node_instances()
        self.assertEqual(1, len(instances))
        self.assertEqual('node', instances[0].node_id)
        return env

    def test_already_initialized_no_reset(self):
        self.test_basic()
        with self.assertRaises(sh.ErrorReturnCode):
            self.test_basic(setup=False, reset=False)

    def test_already_initialized_reset(self):
        self.test_basic()
        self.test_basic(setup=False, reset=True)

    def test_inputs(self):
        env = self.test_basic()
        self.assertEqual(env.outputs()['output'], self.INPUT)

    def test_ignored_modules_sanity(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.test_basic(config_path='ignored_modules_sanity.yaml')
        self.assertIn('No module named', c.exception.stderr)

    def test_ignored_modules(self):
        self.test_basic(config_path='ignored_modules.yaml')

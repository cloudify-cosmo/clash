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

import errno
import os

import sh

from workflowcmd import tests
from workflowcmd.tests import resources


class TestInit(tests.BaseTest):

    INPUT = 'INPUT_VALUE'

    def test_basic(self, setup=True, reset=False, config_path='basic.yaml',
                   editable=False):
        if setup:
            self.dispatch(config_path, 'setup', editable=editable)
            inputs = self.inputs()
            inputs['input'] = self.INPUT
            self.set_inputs(inputs)
        self.dispatch(config_path, 'init', reset=reset)
        env = self.env()
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

    def test_editable_false(self):
        self._test_editable(editable=False)

    def test_editable_true(self):
        self._test_editable(editable=True)

    def _test_editable(self, editable):
        resources_path = self.workdir / '.local' / 'resources'
        self.test_basic(editable=editable)
        self.assertTrue(resources_path.exists())
        if editable:
            expected = resources.DIR / 'blueprints'
            self.assertEqual(os.readlink(resources_path), expected)
        else:
            with self.assertRaises(OSError) as c:
                os.readlink(resources_path)
            self.assertEqual(c.exception.errno, errno.EINVAL)

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

import sh

from clash import tests


class TestEnv(tests.BaseTest):

    def setUp(self):
        super(TestEnv, self).setUp()
        self.config_path = 'basic.yaml'
        self.dispatch(self.config_path, 'env', 'create',
                      name='main',
                      storage_dir=self.workdir / '1')
        self.set_inputs({'input': 'input1'}, name='main')
        self.dispatch(self.config_path, 'init')
        self.dispatch(self.config_path, 'env', 'create',
                      name='second',
                      storage_dir=self.workdir / '2')
        self.set_inputs({'input': 'input2'}, name='second')
        self.dispatch(self.config_path, 'init')

    def test_use(self):
        for name, number in [('main', '1'), ('second', '2')]:
            self.dispatch(self.config_path, 'env', 'use', name)
            status = json.loads(self.dispatch(self.config_path, 'status',
                                              json=True).stdout)
            self.assertEqual(status, {
                'env': {
                    'editable': False,
                    'storage_dir': str(self.workdir / number),
                    'current': name
                },
                'outputs': {
                    'output': 'input{}'.format(number)
                }
            })

    def test_use_no_such_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.dispatch(self.config_path, 'env', 'use', 'what_is_this')
        self.assertIn('No such configuration', c.exception.stderr)

    def test_remove(self):
        self.dispatch(self.config_path, 'env', 'remove', 'second')
        with self.assertRaises(sh.ErrorReturnCode):
            self.dispatch(self.config_path, 'env', 'use', 'second')

    def test_remove_no_such_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.dispatch(self.config_path, 'env', 'remove', 'what_is_this')
        self.assertIn('No such configuration', c.exception.stderr)

    def test_list(self):
        output = self.dispatch(self.config_path, 'env', 'list').stdout.strip()
        names = output.split('\n')
        self.assertEqual(set(names), set(['main', 'second']))

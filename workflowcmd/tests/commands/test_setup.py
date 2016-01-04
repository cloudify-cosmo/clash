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


class TestSetup(tests.BaseTest):

    def test_implicit_storage_dir(self):
        config_path = 'config2.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual(self.workdir, self.storage_dir(config_path))

    def test_explicit_storage_dir(self):
        config_path = 'config2.yaml'
        storage_dir = self.workdir / 'storage'
        self.dispatch(config_path, 'setup', storage_dir=storage_dir)
        self.assertEqual(storage_dir, self.storage_dir(config_path))

    def test_no_inputs(self):
        config_path = 'config2.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual(self.inputs(config_path), {})

    def test_after_setup(self):
        config_path = 'after_setup.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual((self.workdir / 'after_setup').text(),
                         self.config(config_path)['name'])

    def test_args_and_parse_parameters(self):
        config_path = 'setup_args.yaml'
        arg1 = 'arg1_value'
        arg2 = 'arg2_value'
        self.dispatch(config_path, 'setup', arg1, arg2=arg2)
        self.assertEqual(self.inputs(config_path),
                         {'arg1': arg1, 'arg2': arg2})

    def test_inputs(self):
        config_path = 'setup_inputs.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual(self.inputs(config_path), {
            'input1': 'input1_default',
            'input2': 'input2_setup',
            'input3': '_',
            'input4': 'input4_setup'
        })

    def test_storage_dir_already_configured_no_reset(self):
        config_path = 'config2.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual(self.storage_dir(config_path), self.workdir)
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.dispatch(config_path, 'setup')
        self.assertIn('already configured', c.exception.stderr)
        self.assertEqual(self.storage_dir(config_path), self.workdir)

    def test_storage_dir_already_configured_reset(self):
        config_path = 'config2.yaml'
        self.dispatch(config_path, 'setup')
        self.assertEqual(self.storage_dir(config_path), self.workdir)
        storage_dir = self.workdir / 'storage'
        self.dispatch(config_path, 'setup',
                      storage_dir=storage_dir,
                      reset=True)
        self.assertEqual(self.storage_dir(config_path), storage_dir)


def after_setup(loader):
    with open('after_setup', 'w') as f:
        f.write(loader.config['name'])

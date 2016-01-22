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


class TestEnvCreate(tests.BaseTest):

    def test_default_name(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.current(), 'main')

    def test_explicit_name(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create', name='second')
        self.assertEqual(self.current(), 'second')

    def test_implicit_storage_dir(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.workdir, self.storage_dir())

    def test_explicit_storage_dir(self):
        config_path = 'plain.yaml'
        storage_dir = self.workdir / 'storage'
        self.dispatch(config_path, 'env', 'create', storage_dir=storage_dir)
        self.assertEqual(storage_dir, self.storage_dir())

    def test_no_inputs(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.inputs(), {})

    def test_editable_default(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertFalse(self.editable())

    def test_editable_true(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create', editable=True)
        self.assertTrue(self.editable())

    def test_after_env_create(self):
        arg1 = 'arg1_value'
        arg2 = 'arg2_value'
        config_path = 'after_env_create.yaml'
        self.dispatch(config_path, 'env', 'create', arg1, arg2)
        self.assertEqual(
                json.loads((self.workdir / 'after_env_create').text()),
                {'name': self.config(config_path)['name'],
                 'arg1': arg1,
                 'arg2': arg2})

    def test_args_and_parse_parameters(self):
        config_path = 'env_create_args.yaml'
        arg1 = 'arg1_value'
        arg2 = 'arg2_value'
        self.dispatch(config_path, 'env', 'create', arg1, arg2=arg2)
        self.assertEqual(self.inputs(),
                         {'arg1': arg1, 'arg2': arg2})

    def test_inputs(self):
        config_path = 'env_create_inputs.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.inputs(), {
            'input1': 'input1_default',
            'input2': 'input2_env_create',
            'input3': '_',
            'input4': 'input4_env_create'
        })
        inputs_path = self.storage_dir() / 'inputs.yaml'
        inputs_text = inputs_path.text()
        self.assertTrue(inputs_text.startswith(
            '# This is the description for the blueprint'))
        self.assertIn('# This is the description for input1\ninput1:',
                      inputs_text)
        self.assertIn('# This is the description for input2\ninput2:',
                      inputs_text)

    def test_storage_dir_already_configured_no_reset(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.storage_dir(), self.workdir)
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.dispatch(config_path, 'env', 'create')
        self.assertIn('already configured', c.exception.stderr)
        self.assertEqual(self.storage_dir(), self.workdir)
        self.assertFalse(self.editable())

    def test_storage_dir_already_configured_reset(self):
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.storage_dir(), self.workdir)
        storage_dir = self.workdir / 'storage'
        self.dispatch(config_path, 'env', 'create',
                      storage_dir=storage_dir,
                      reset=True)
        self.assertEqual(self.storage_dir(), storage_dir)
        self.assertFalse(self.editable())

    def test_storage_dir_already_configured_different_name_no_reset(self):
        storage_dir2 = self.workdir / 's2'
        config_path = 'plain.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.assertEqual(self.storage_dir(), self.workdir)
        self.dispatch(config_path, 'env', 'create', name='second',
                      storage_dir=storage_dir2, editable=True)
        self.assertEqual(self.storage_dir(), self.workdir)
        self.assertFalse(self.editable())
        self.assertEqual(self.storage_dir('second'), storage_dir2)
        self.assertTrue(self.editable('second'))

    def test_generated_macros_yaml(self):
        config_path = 'plain.yaml'
        macros_path = self.workdir / 'macros.yaml'
        self.assertFalse(macros_path.isfile())
        self.dispatch(config_path, 'env', 'create')
        self.assertTrue(macros_path.isfile())


def after_env_create(loader, arg1, arg2, **kwargs):
    with open('after_env_create', 'w') as f:
        f.write(json.dumps({
            'name': loader.config['name'],
            'arg1': arg1,
            'arg2': arg2
        }))

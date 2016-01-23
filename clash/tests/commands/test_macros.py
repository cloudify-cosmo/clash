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

import copy

import json
import yaml
import sh

from clash import tests


class TestMacros(tests.BaseTest):

    def test_basic_macro(self):
        self._test_macro(command=['macro1'])

    def test_nested_macro(self):
        self._test_macro(command=['nested', 'macro2'])

    def test_nested_macro2(self):
        self._test_macro(command=['nested2', 'macro3'])

    def test_failed_macro(self):
        config_path = 'end_to_end.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.dispatch(config_path, 'init')
        macros = {
            'fail-macro': {'commands': [
                {'name': 'command1',
                 'args': ['a', '-a', 'a2', '--output-path', 'fail']}
            ]}
        }
        macros_path = self.workdir / 'macros.yaml'
        macros_path.write_text(yaml.safe_dump(macros))
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.dispatch(config_path, 'fail-macro')
        self.assertIn('from workflow1', c.exception.stdout)
        self.assertIn('EXPECTED', c.exception.stderr)

    def test_update_python_path(self):
        config_path = 'pythonpath.yaml'
        storage_dir_functions = self.workdir / 'storage_dir_functions'
        storage_dir_functions.mkdir_p()
        (storage_dir_functions / '__init__.py').touch()
        script_path = storage_dir_functions / 'functions.py'
        script_path.write_text('def func2(**_): return "2"')
        macros = {
            'macro-func': {
                'commands': [
                    {'name': 'command2',
                     'args': [
                         '--arg1',
                         {'func': {
                             'name': 'blueprint_functions.functions:func1'}},
                         '--arg2',
                         {'func': {
                             'name': 'storage_dir_functions.functions:func2'}}
                     ]}
                ]
            }
        }
        macros_path = self.workdir / 'macros.yaml'
        macros_path.write_text(yaml.safe_dump(macros))
        self.dispatch(config_path, 'env', 'create')
        self.dispatch(config_path, 'init')
        output = self.dispatch(config_path, 'macro-func').stdout
        self.assertIn('param1: 1, param2: 2', output)

    def _test_macro(self, command):
        config_path = 'end_to_end.yaml'
        output1_path = self.workdir / 'output1.json'
        output2_path = self.workdir / 'output2.json'
        self.dispatch(config_path, 'env', 'create')
        self.dispatch(config_path, 'init')

        macro = {
            'args': [
                {'name': '--arg1-1'},
                {'name': '--arg3-1'},
                {'name': '--arg1-2'},
                {'name': '--arg3-2'},
                {'name': '--out1'},
                {'name': '--out2'}
            ],
            'commands': [
                {'name': 'command1',
                 'args': [
                     {'arg': 'arg1_1'},
                     '--arg3', {'arg': 'arg3_1'},
                     '--output-path', {'arg': 'out1'}
                 ]},
                {'name': 'command1',
                 'args': [
                     {'arg': 'arg1_2'},
                     '--arg3', {'arg': 'arg3_2'},
                     '--output-path', {'arg': 'out2'}
                 ]}
            ]
        }

        macros = {
            'macro1': copy.deepcopy(macro),
            'nested': {
                'macro2': copy.deepcopy(macro)
            },
            'nested2': {
                'macro3': copy.deepcopy(macro)
            }
        }
        macros_path = self.workdir / 'macros.yaml'
        macros_path.write_text(yaml.safe_dump(macros))

        output = self.dispatch(config_path, command,
                               arg1_1='arg1_1_value',
                               arg3_1='arg3_1_value',
                               arg1_2='arg1_2_value',
                               arg3_2='arg3_2_value',
                               out1=output1_path,
                               out2=output2_path).stdout
        self.assertEqual(json.loads(output1_path.text()), {
            'param1': 'arg1_1_value',
            'param2': 'arg2_default',
            'param3': 'arg3_1_value'
        })
        self.assertEqual(json.loads(output2_path.text()), {
            'param1': 'arg1_2_value',
            'param2': 'arg2_default',
            'param3': 'arg3_2_value'
        })
        self.assertIn('from workflow1', output)

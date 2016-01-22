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
import json

from mock import patch

from clash import tests


class TestApply(tests.BaseTest):

    def test_basic(self):
        self._test(verbose=False)

    def test_verbose(self):
        self._test(verbose=True)

    def test_nested(self):
        self._test(config_path='apply_nested.yaml')

    def _test(self, verbose=False, config_path='apply.yaml'):
        output_path = self.workdir / 'output.json'
        expected = {
            'param1': 'param1_value',
            'param2': 'param2_value',
            'param3': 'param3_value'
        }

        def assert_output(out):
            assertion = self.assertIn if verbose else self.assertNotIn
            assertion('workflow execution succeeded', out)

        with patch.dict(os.environ, {'test_output_path': output_path}):
            self.assertFalse(output_path.exists())
            self.dispatch(config_path, 'env', 'create')
            output = self.dispatch(config_path, 'apply',
                                   verbose=verbose).stdout.strip()
            assert_output(output)
            self.assertEqual(expected, json.loads(output_path.text()))
            output_path.remove()
            self.assertFalse(output_path.exists())
            output = self.dispatch(config_path, 'apply',
                                   verbose=verbose).stdout.strip()
            assert_output(output)
            self.assertEqual(expected, json.loads(output_path.text()))

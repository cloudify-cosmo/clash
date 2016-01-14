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

    def test_apply(self):
        config_path = 'apply.yaml'
        output_path = self.workdir / 'output.json'
        expected = {
            'param1': 'param1_value',
            'param2': 'param2_value',
            'param3': 'param3_value'
        }
        with patch.dict(os.environ, {'test_output_path': output_path}):
            self.assertFalse(output_path.exists())
            self.dispatch(config_path, 'env', 'create')
            self.dispatch(config_path, 'apply')
            self.assertEqual(expected, json.loads(output_path.text()))
            output_path.remove()
            self.assertFalse(output_path.exists())
            self.dispatch(config_path, 'apply')
            self.assertEqual(expected, json.loads(output_path.text()))

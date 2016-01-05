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

from dsl_parser import functions as dsl_functions


def parse_parameters(loader, parameters, args):
    functions = {
        'arg': lambda func_args: args[func_args],
        'env': lambda func_args: os.environ[func_args],
        'loader': lambda func_args: getattr(loader, func_args)
    }
    for name, process in functions.items():
        dsl_functions.register(_function(process), name)
    try:
        return dsl_functions.evaluate_functions(parameters,
                                                None, None, None, None)
    finally:
        for name in functions.keys():
            dsl_functions.unregister(name)


def _function(process):
    class Function(dsl_functions.Function):
        validate = None
        evaluate = None
        function_args = None

        def parse_args(self, args):
            self.function_args = args

        def evaluate_runtime(self, **_):
            return process(self.function_args)
    return Function

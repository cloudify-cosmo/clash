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

from clash import module

_RAW = object()


def parse_parameters(loader, parameters, args):

    def env(func_args):
        if not isinstance(func_args, list):
            func_args = [func_args]
        return os.environ.get(*func_args)

    def func(func_args):
        kwargs = func_args.get('kwargs', {})
        for value in kwargs.values():
            if dsl_functions.parse(value) != value:
                return _RAW
        kwargs['loader'] = loader
        function = module.load_attribute(func_args['name'])
        return function(**kwargs)

    functions = {
        'env': env,
        'arg': lambda func_args: args[func_args],
        'user_config': lambda func_args: getattr(loader.user_config,
                                                 func_args),
        'loader': lambda func_args: getattr(loader, func_args),
        'func': func
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
            result = process(self.function_args)
            if result is _RAW:
                return self.raw
            return result
    return Function

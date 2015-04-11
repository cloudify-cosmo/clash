import importlib
import sys
import os
import shutil

import yaml
import argh
from path import path
from cloudify_cli import utils as cli_utils
from cloudify.workflows import local
from dsl_parser import functions as dsl_functions


class Loader(object):

    def __init__(self, package, config_path, storage_dir, blueprint_path):
        package = importlib.import_module(package)
        package_path = path(package.__file__).dirname()
        config_path = package_path / config_path
        self.config = yaml.load(config_path.text())
        self.blueprint_path = config_path.dirname() / blueprint_path
        self.blueprint_dir = self.blueprint_path.dirname()
        self.storage_dir = path(os.path.expanduser(storage_dir))
        self.parser = argh.ArghParser()
        self._parse_commands(commands=self.config['commands'])
        self.parser.add_commands(functions=[self._init_command])

    def _parse_commands(self, commands, namespace=None):
        functions = []
        for name, command in commands.items():
            if 'workflow' not in command:
                self._parse_commands(commands=command, namespace=name)
                continue
            functions.append(self._parse_command(name=name, command=command))
        self.parser.add_commands(functions=functions, namespace=namespace)

    def _parse_command(self, name, command):
        @argh.expects_obj
        @argh.named(name)
        def func(args):
            args = vars(args)
            parameters = _parse_parameters(command.get('parameters', {}), args)
            task_config = {
                'retries': 0,
                'retry_interval': 1,
                'thread_pool_size': 1
            }
            global_task_config = self.config.get('task', {})
            command_task_config = command.get('task', {})
            task_config.update(global_task_config)
            task_config.update(command_task_config)
            sys.path.append(self.storage_dir / 'local' / 'resources')
            env = local.load_env(name='local',
                                 storage=self._storage())
            env.execute(workflow=command['workflow'],
                        parameters=parameters,
                        task_retries=task_config['retries'],
                        task_retry_interval=task_config['retry_interval'],
                        task_thread_pool_size=task_config['thread_pool_size'])

        for arg in reversed(command.get('args', [])):
            name = arg.pop('name')
            if not isinstance(name, list):
                name = [name]
            argh.arg(*name, **arg)(func)

        return func

    def _storage(self):
        return local.FileStorage(storage_dir=self.storage_dir)

    @argh.named('init')
    def _init_command(self, inputs=None, reset=False):
        name = 'local'
        local_dir = self.storage_dir / name
        if local_dir.exists() and reset:
            shutil.rmtree(local_dir)
        inputs = cli_utils.inputs_to_dict(inputs, 'inputs')
        sys.path.append(self.blueprint_dir)
        local.init_env(blueprint_path=self.blueprint_path,
                       inputs=inputs,
                       name=name,
                       storage=self._storage())

    def dispatch(self):
        self.parser.dispatch()


def dispatch(package, config_path, storage_dir, blueprint_path):
    loader = Loader(package=package,
                    config_path=config_path,
                    storage_dir=storage_dir,
                    blueprint_path=blueprint_path)
    loader.dispatch()


def _parse_parameters(parameters, args):
    class Arg(dsl_functions.Function):
        validate = None
        evaluate = None

        def parse_args(self, _args):
            self.arg = _args

        def evaluate_runtime(self, *_, **__):
            return args[self.arg]

    dsl_functions.register(Arg, 'arg')
    try:
        return dsl_functions.evaluate_functions(parameters,
                                                None, None, None, None)
    finally:
        dsl_functions.unregister('arg')

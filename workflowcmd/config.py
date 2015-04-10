import importlib
import sys
import os
import shutil

import yaml
import argh
from path import path
from cloudify_cli import utils as cli_utils
from cloudify.workflows import local


def load(package, config_path, storage_dir):

    package = importlib.import_module(package)
    package_path = path(package.__file__).dirname()
    config_path = package_path / config_path
    config = yaml.load(config_path.text())
    commands = config['commands']
    parser = argh.ArghParser()

    blueprint_path = config_path.dirname() / config['blueprint']
    blueprint_dir = blueprint_path.dirname()
    storage_dir = path(os.path.expanduser(storage_dir))

    _parse_commands(parser, commands, config, storage_dir)

    def init(inputs=None, reset=False):
        name = 'local'
        if (storage_dir / name).exists() and reset:
            shutil.rmtree(storage_dir / name)
        inputs = cli_utils.inputs_to_dict(inputs, 'inputs')
        sys.path.append(blueprint_dir)
        local.init_env(blueprint_path,
                       inputs=inputs,
                       name=name,
                       storage=_storage(storage_dir))

    argh.add_commands(parser, [init])
    argh.dispatch(parser)


def _parse_commands(parser, commands, config, storage_dir, namespace=None):
    functions = []
    for name, command in commands.items():
        if command.get('_nested'):
            command.pop('_nested')
            _parse_commands(parser, command, config, storage_dir,
                            namespace=name)
            continue
        functions.append(_parse_command(name, command, config, storage_dir))
    argh.add_commands(parser,
                      functions=functions,
                      namespace=namespace)


def _parse_command(name, command, config, storage_dir):
    def func(*args, **kwargs):
        task_config = {
            'retries': 0,
            'retry_interval': 1,
            'thread_pool_size': 1
        }
        global_task_config = config.get('task', {})
        command_task_config = command.get('task', {})
        task_config.update(global_task_config)
        task_config.update(command_task_config)

        sys.path.append(storage_dir / 'local' / 'resources')
        env = local.load_env(name='local',
                             storage=_storage(storage_dir))

        env.execute(workflow=command['workflow'],
                    parameters=command.get('parameters'),
                    task_retries=task_config['retries'],
                    task_retry_interval=task_config['retry_interval'],
                    task_thread_pool_size=task_config['thread_pool_size'])

    func.__name__ = name

    return func


def _storage(storage_dir):
    return local.FileStorage(storage_dir=storage_dir)

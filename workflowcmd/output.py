import sys

import colors
from cloudify import logs

from workflowcmd import util


class _Event(dict):

    def __init__(self, event):
        self.update(event)

    @property
    def context(self):
        return self.get('context', {})

    @property
    def blueprint_id(self):
        return self.context.get('blueprint_id')

    @property
    def deployment_id(self):
        return self.context.get('deployment_id')

    @property
    def execution_id(self):
        return self.context.get('execution_id')

    @property
    def workflow_id(self):
        return self.context.get('workflow_id')

    @property
    def task_id(self):
        return self.context.get('task_id')

    @property
    def task_name(self):
        return self.context.get('task_name')

    @property
    def task_target(self):
        return self.context.get('task_target')

    @property
    def operation(self):
        return self.context.get('operation')

    @property
    def plugin(self):
        return self.context.get('plugin')

    @property
    def node_instance_id(self):
        return self.context.get('node_id')

    @property
    def node_id(self):
        return self.node_name

    @property
    def node_name(self):
        return self.context.get('node_name')

    @property
    def source_node_instance_id(self):
        return self.context.get('source_id')

    @property
    def source_node_id(self):
        return self.source_node_id

    @property
    def source_node_name(self):
        return self.context.get('source_name')

    @property
    def target_node_instance_id(self):
        return self.context.get('target_id')

    @property
    def target_node_id(self):
        return self.target_node_name

    @property
    def target_node_name(self):
        return self.context.get('target_name')

    @property
    def logger(self):
        return self.get('logger')

    @property
    def level(self):
        return self.get('level')

    @property
    def message(self):
        return self.get('message', {}).get('text', '').encode('utf-8')

    @property
    def timestamp(self):
        return self.get('@timestamp') or self.get('timestamp')

    @property
    def message_code(self):
        return self.get('message_code')

    @property
    def type(self):
        return self.get('type')

    @property
    def event_type(self):
        return self.get('event_type')


def _default_output_handler(event, env):
    operation = None
    if event.operation is not None:
        operation = event.operation.split('.')[-1]
        operation = colors.magenta(operation)
    if event.source_node_name is not None:
        source_name = colors.cyan(event.source_node_name)
        target_name = colors.cyan(event.target_node_name)
        info = '{}->{}|{}'.format(source_name, target_name, operation)
    else:
        node_name = event.node_name
        if node_name:
            node_name = colors.cyan(node_name)
        info_elements = filter(None, [node_name, operation])
        info = '.'.join(info_elements)
    if info:
        info = '[{}] '.format(info)
    message = event.message
    if event.event_type == 'task_succeeded':
        message = colors.color(message, fg=10)
    elif event.event_type == 'task_failed':
        message = colors.color(message, fg=9)
    elif event.event_type == 'task_rescheduled':
        message = colors.color(message, fg=11)

    if event.level:
        level = event.level.upper()
        if 'INFO' in level:
            level = colors.green(level)
        elif 'WARN' in level:
            level = colors.yellow(level)
        elif 'ERROR' in level:
            level = colors.red(level)
        message = '{}: {}'.format(level, message)
    return '{}{}'.format(info, message)


def _load_output_handler(output_handler):
    if not output_handler:
        return _default_output_handler
    return util.load_attribute(output_handler)


def _process_event(output_handler, event, env):
    processed_event = output_handler(event=_Event(event),
                                     env=env)
    if not processed_event:
        return
    sys.stdout.write('{}\n'.format(processed_event))


def setup_output(output_handler, verbose, env):
    output_handler = _load_output_handler(output_handler)

    def stdout_event_out(event):
        if not verbose:
            return
        logs.populate_base_item(event, 'cloudify_event')
        _process_event(output_handler, event, env)

    def stdout_log_out(event):
        logs.populate_base_item(event, 'cloudify_log')
        _process_event(output_handler, event, env)

    logs.stdout_event_out = stdout_event_out
    logs.stdout_log_out = stdout_log_out

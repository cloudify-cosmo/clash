import json

from cloudify.workflows import parameters, ctx

output_path = parameters.output_path

with open(output_path, 'w') as f:
    f.write(json.dumps({
        'retries': ctx._task_retries,
        'retry_interval': ctx._task_retry_interval,
        'thread_pool_size': ctx._local_task_thread_pool_size
    }))

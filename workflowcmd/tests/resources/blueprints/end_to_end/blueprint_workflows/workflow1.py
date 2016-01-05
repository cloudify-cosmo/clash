import json

from cloudify.workflows import parameters

output_path = parameters.output_path
param1 = parameters.param1
param2 = parameters.param2
param3 = parameters.param3

with open(output_path, 'w') as f:
    f.write(json.dumps({
        'param1': param1,
        'param2': param2,
        'param3': param3
    }))

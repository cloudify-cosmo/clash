from cloudify.workflows import ctx
from cloudify.workflows import parameters


ctx.logger.info('param1: {0}, param2: {1}'.format(parameters.param1,
                                                  parameters.param2))
instance = next(ctx.node_instances)
instance.execute_operation('interface.op')

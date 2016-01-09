from cloudify.workflows import ctx

instance = next(ctx.node_instances)
instance.execute_operation('interface.op')

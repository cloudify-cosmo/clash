from cloudify import ctx
from cloudify.decorators import operation


@operation
def op(**kwargs):
    ctx.logger.info('all good')

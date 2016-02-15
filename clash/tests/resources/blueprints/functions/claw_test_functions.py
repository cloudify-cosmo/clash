from clash import ctx


def testing_function(arg1, arg2=None):
    return '{} {} {}'.format(arg1, arg2, ctx.config.name)

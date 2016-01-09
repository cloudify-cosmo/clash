from clash import output


class Event1(output.Event):

    def __str__(self):
        return 'EVENT1'


class Event2(output.Event):

    def __str__(self):
        return 'EVENT2'


class Event3Factory(object):

    @staticmethod
    def factory(env, verbose):
        class Event3(output.Event):
            def __str__(self):
                return 'EVENT3 env: {0}, verbose: {1}'.format(env.name,
                                                              verbose)
        return Event3

from twisted.python import usage # type: ignore

class Options(usage.Options):
    optParameters = [
        ['servdir', 's', './', 'The directory to switch to and run from.'],
        ['config-file', 'c', None, 'The directory containing the configuration file.']
    ]

from pickle import load

fname = 'src/cipolla/data/tracing.pickle'

exceptions = []
with open(fname, 'rb') as fp:
    while 1:
        try:
            exceptions.append(load(fp))
        except EOFError:
            break

from IPython import embed; embed()

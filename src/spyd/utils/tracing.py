import logging

logger = None
indent = 0

def setup_logger(filename):
    global logger
    assert logger is None

    logging.basicConfig(level = logging.DEBUG)

    console = logging.FileHandler(filename)
    console.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s | %(levelname)s: %(message)s')
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)

    logger = logging.getLogger('debug')
    logger.addHandler(console)

def started(f_id, func, args, kw):
    global indent
    indent += 2
    bg = f"{' '*(indent-2)}|\n{' '*(indent-2)}+-> |START|{f_id}| "
    printExecution(bg, func, f'{args}, {kw}')

def ended(f_id, func):
    global indent
    indent -= 2
    bg = f"{' '*(indent)}+{' '*(indent)} | END |{f_id}| "
    printExecution(bg, func, '')

def raised(f_id, func, e):
    global indent
    indent -= 2
    bg = f"{' '*(indent)}+{' '*(indent)} | RAISE |{f_id}| "
    printExecution(bg, func, '{'+str(e)+'}')

def printExecution(beginStr, func, argStr):
    assert logger is not None
    logger.debug(f"{beginStr} {func}: {argStr}")

def function_id(func, args, kwargs):
    from hashlib import md5

    data = f"{id(func)}|{args}|{kwargs}".encode('utf-8')
    return md5(data).hexdigest()

progressiveId = 0

def tracer(func):
    def dump_exception(fname, e):
        from pickle import dump
        with open(fname, 'wb') as fp:
            dump(e, fp) # one at time, read it until eof

    def inner(*args, **kwargs):
        import traceback
        # f_id = function_id(func, args, kwargs)
        global progressiveId
        progressiveId += 1
        f_id = progressiveId
        started(f_id, func, args, kwargs)
        try:
            res = func(*args, **kwargs)
            ended(f_id, func)
            return res
        except Exception as e:
            raised(f_id, func, e)
            tb = traceback.format_exc()
            dump_exception('tracing.pickle', (e, tb))
            raise e
    return inner

def decorator_to_all_members(cls, dec):
    import inspect
    import types
    for name, fn in inspect.getmembers(cls):
        if isinstance(fn, types.FunctionType):
            setattr(cls, name, dec(fn))

def trace_class(cls):
    decorator_to_all_members(cls, tracer)

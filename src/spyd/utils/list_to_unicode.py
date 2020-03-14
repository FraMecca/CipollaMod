def to_unicode(i):
    if not isinstance(i, str):
        i = str(i, 'utf_8')
    return i

def list_to_unicode(l):
    return [to_unicode(i) for i in l]

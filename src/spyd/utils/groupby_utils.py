def unroll_group(kv):
    by, group = kv
    return by, list(group)
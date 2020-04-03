def filtertext(src: str, whitespace: bool, maxlen: int) -> str:
    last_was_ctrl_char = [False]

    def allowchar(c):
        if last_was_ctrl_char[0]:
            last_was_ctrl_char[0] = False
            return False

        if not whitespace and c.isspace():
            return False

        if c == '\f':
            last_was_ctrl_char[0] = True
            return False

        return True

    dst = ''.join(filter(allowchar, src))

    if len(dst) > maxlen:
        dst = dst[:maxlen]

    return dst

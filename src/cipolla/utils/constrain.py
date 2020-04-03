class ConstraintViolation(Exception):
    def __init__(self, message, constraint_name):
        self.constraint_name = constraint_name
        Exception.__init__(self, message)

def constrain_range(value: int, minimum: int, maximum: int, constraint_name: str) -> None:
    if value < minimum or value > maximum:
        raise ConstraintViolation("{} not in range ({}, {})".format(value, minimum, maximum), constraint_name)

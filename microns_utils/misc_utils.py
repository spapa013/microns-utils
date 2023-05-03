"""
Misc utils
"""

class classproperty:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def wrap(item):
    if isinstance(item, (list, tuple)):
        return item
    else:
        return item,


def unwrap(item):
    if isinstance(item, (list, tuple)):
        if len(item) == 1:
            return item[0]
    else:
        return item
    

def sc_to_ucc(string):
    """
    formats snake_case str as UpperCamelCase
    """
    return ''.join(string.title().split('_'))
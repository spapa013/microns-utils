from datajoint_plus.utils import classproperty, wrap, unwrap

def sc_to_ucc(string):
    """
    formats snake_case str as UpperCamelCase
    """
    return ''.join(string.title().split('_'))
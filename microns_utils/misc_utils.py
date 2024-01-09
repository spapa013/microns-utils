"""
Misc utils
"""

class classproperty:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def wrap(item, return_as_list=False):
    if isinstance(item, (list, tuple)):
        return item
    else:
        if not return_as_list:
            return item,
        else:
            return list(item),


def unwrap(item, enforce_one_item=False):
    if isinstance(item, (list, tuple)):
        if len(item) == 1:
            return item[0]
        else:
            if enforce_one_item:
                raise ValueError(f"Expected length 1, got length {len(item)}")
            else:
                return item
    else:
        return item
    

def sc_to_ucc(string):
    """
    formats snake_case str as UpperCamelCase
    """
    return ''.join(string.title().split('_'))


class FieldDict(dict):
    """
    FieldDict is an enhanced dictionary that allows attribute-style access 
    to its keys, in addition to the standard dictionary-style access. 
    It also automatically converts nested dictionaries to FieldDict instances, 
    enabling recursive attribute-style access.

    Example:
        fd = FieldDict(a=1, b={'c': 2, 'd': {'e': 3}})
        print(fd.a)  # Outputs 1
        print(fd.b.d.e)  # Outputs 3

    Attributes are accessed just like dictionary keys. If an attribute does not exist,
    AttributeError is raised.
    """
    def __init__(self, **kwargs):
        """
        Initialize a FieldDict instance. All keyword arguments provided are set as keys 
        and values of the dictionary. Nested dictionaries are automatically converted 
        to FieldDict instances.

        Args:
            **kwargs: Arbitrary keyword arguments. Each keyword becomes a key in the 
                      FieldDict, and the corresponding value becomes the value.
            
            Optional keyword arguments:
                _name (str, optional): The name of the FieldDict instance. Defaults to "FieldDict".
                _key_disp_limit (int, optional): The maximum number of keys to display when a FieldDict object is accessed. 
                    Key display can be disabled by setting to 0 or None. Defaults to 4.
        """
        for param, default_value in self._defaults.items():
            setattr(self, param, kwargs.pop(param, default_value))
        
        super().__init__()
        for key, value in kwargs.items():
            self[key] = self._convert(value)
    
    _defaults = {'_name': "FieldDict", '_key_disp_limit': 4}

    def __setitem__(self, key, value):
        super(FieldDict, self).__setitem__(key, self._convert(value))

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'FieldDict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            # Handle setting of private and protected attributes normally
            super(FieldDict, self).__setattr__(name, value)
        else:
            self[name] = self._convert(value)

    def __delattr__(self, name):
        if name.startswith('_'):
            # Handle deletion of private and protected attributes normally
            super(FieldDict, self).__delattr__(name)
        else:
            del self[name]

    def __repr__(self):
        keys = list(self.keys())
        len_keys = len(keys)
        key_disp_limit = self._key_disp_limit or 0
        name = self._name or "FieldDict"
        prefix = f"<{name} object at {hex(id(self))}"

        if len_keys == 1:
            key_len_repr = f" with 1 key"
        else:
            key_len_repr = f" with {len_keys} keys"

        if len_keys == 0 or key_disp_limit == 0:
            return prefix + key_len_repr + ">"

        if key_disp_limit == 1:
            if len_keys == 1:
                key_disp_repr = f": '{keys[0]}'>"
            else:
                key_disp_repr = f": '{keys[0]}', ... >" 
            return prefix + key_len_repr + key_disp_repr

        if len_keys > key_disp_limit:
            key_disp_repr = ", ".join(f"'{k}'" for k in keys[:key_disp_limit//2]) + ", ..., " + ", ".join(f"'{k}'" for k in keys[-key_disp_limit//2:])
        else:
            key_disp_repr = ", ".join(f"'{k}'" for k in keys)
        key_disp_repr = f": {key_disp_repr}>"
        return prefix + key_len_repr + key_disp_repr

    def get_with_path(self, path, default=None):
        """
        Retrieve a value from the FieldDict using a dot-separated path. If the path 
        does not exist, the method returns the specified default value.

        Example:
            fd = FieldDict(a=1, b={'c': 2, 'd': {'e': 3}})
            value = fd.get_with_path('b.d.e')  # Returns 3

        Args:
            path (str): A dot-separated path string indicating the nested keys. 
                        For example, 'a.b.c' refers to the path dict['a']['b']['c'].
            default (any, optional): The default value to return if the path is not found.
                                     Defaults to None.

        Returns:
            The value found at the path, or the default value if the path is not found.
        """
        keys = path.split('.')
        current = self
        for key in keys:
            if key in current:
                current = current[key]
            else:
                return default
        return current

    gwp = get_with_path # alias for get_with_path

    @staticmethod
    def _convert(value):
        if isinstance(value, dict) and not isinstance(value, FieldDict):
            return FieldDict(**value)
        elif isinstance(value, (list, set, tuple)):
            return type(value)(FieldDict._convert(v) for v in value)
        return value
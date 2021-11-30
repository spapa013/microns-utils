"""
Methods for configuring microns packages.
"""

import traceback
import inspect
try:
    import datajoint as dj
except:
    traceback.print_exc()
    raise ImportError('DataJoint package not found.')
import datajoint.datajoint_plus as djp

def enable_datajoint_flags(enable_python_native_blobs=True):
    """
    Enable experimental datajoint features
    
    These flags are required by 0.12.0+ (for now).
    """
    dj.config['enable_python_native_blobs'] = enable_python_native_blobs
    dj.errors._switch_filepath_types(True)
    dj.errors._switch_adapted_types(True)


def register_externals(external_stores):
    """
    Registers the external stores for a schema_name in this module.
    """
    if 'stores' not in dj.config:
        dj.config['stores'] = external_stores
    else:
        dj.config['stores'].update(external_stores)


def make_store_dict(path):
    return {
        'protocol': 'file',
        'location': str(path),
        'stage': str(path)
    }


def _get_calling_context() -> locals:
    # get the calling namespace
    import inspect
    try:
        frame = inspect.currentframe().f_back
        context = frame.f_locals
    finally:
        del frame
    return context


def register_adapters(adapter_objects, context=None):
    """
    Imports the adapters for a schema_name into the global namespace.
    """   
    if context is None:
        # if context is missing, use the calling namespace
        import inspect
        try:
            frame = inspect.currentframe().f_back
            context = frame.f_locals
        finally:
            del frame
    
    for name, adapter in adapter_objects.items():
        context[name] = adapter


def register_bases(base, module):
    """
    Recursive function that adds __bases__ from DataJoint Tables in base to matching classes in module.
    :param base (module): source module with classes to. 
    :param module (module): mapping between classes and methods
    """
    for name in dir(base):
        if hasattr(module, name) and inspect.isclass(getattr(module, name)) and issubclass(getattr(module, name), dj.Table):
            base_cls, module_cls = getattr(base, name), getattr(module, name)
            assert base_cls not in module_cls.__bases__, f'Class "{name}" of base already in __base__ of module.'
            module_cls.__bases__ = (base_cls, *module_cls.__bases__)
            register_bases(base_cls, module_cls)


djp_mapping = {
    'Lookup': djp.VirtualLookup,
    'Manual': djp.VirtualManual,
    'Computed': djp.VirtualComputed,
    'Imported': djp.VirtualImported,
    'Part': djp.VirtualPart
}


def add_datajoint_plus(module):
    """
    Adds DataJointPlus recursively to the DataJoint tables inside the module.
    """
    for name in dir(module):
        obj = getattr(module, name)
        if inspect.isclass(obj) and issubclass(obj, dj.Table) and not issubclass(obj, djp.VirtualModule):
            obj.__bases__ = (djp_mapping[obj.__base__.__name__],)
            obj.parse_hash_info_from_header()
            add_datajoint_plus(obj)


def _create_vm(schema_name:str, external_stores=None, adapter_objects=None):
    """
    Creates a virtual module after registering the external stores, and includes the adapter objects in the vm. 

    Creating tables disabled from virtual modules. 
    """
    
    if external_stores is not None:
        register_externals(external_stores)
    
    return dj.create_virtual_module(schema_name, schema_name, add_objects=adapter_objects, create_tables=False)

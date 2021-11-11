import traceback

try:
    import datajoint as dj
except:
    traceback.print_exc()
    raise ImportError('DataJoint package not found.')


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


def create_vm(schema_name:str, external_stores=None, adapter_objects=None):
    """
    Creates a virtual module after registering the external stores, and includes the adapter objects in the vm. 

    Creating tables disabled from virtual modules. 
    """
    
    if external_stores is not None:
        register_externals(external_stores)
    
    return dj.create_virtual_module(schema_name, schema_name, add_objects=adapter_objects, create_tables=False)
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


djp_mapping = {
    'Lookup': djp.Lookup,
    'Manual': djp.Manual,
    'Computed': djp.Computed,
    'Imported': djp.Imported,
    'Part': djp.Part
}


djp_virtual_mapping = {
    'Lookup': djp.VirtualLookup,
    'Manual': djp.VirtualManual,
    'Computed': djp.VirtualComputed,
    'Imported': djp.VirtualImported,
    'Part': djp.VirtualPart
}


def add_datajoint_plus(module, virtual=False):
    """
    Adds DataJointPlus recursively to the DataJoint tables inside the module.
    """
    for name in dir(module):
        obj = getattr(module, name)
        if virtual:
            if inspect.isclass(obj) and issubclass(obj, dj.Table) and not issubclass(obj, djp.VirtualModule):
                obj.__bases__ = (djp_virtual_mapping[obj.__base__.__name__],)
                obj.parse_hash_info_from_header()
                add_datajoint_plus(obj)
        else:
            if inspect.isclass(obj) and issubclass(obj, dj.Table) and not issubclass(obj, djp.Base):
                obj.__bases__ = (djp_mapping[obj.__base__.__name__],) if not virtual else (djp_virtual_mapping[obj.__base__.__name__],)
                obj.parse_hash_info_from_header()
                add_datajoint_plus(obj)


def reassign_master_attribute(module):
    """
    Overwrite .master attribute in DataJoint part tables to map to master class from current module instead of inherited module
    """
    for name in dir(module):
        # Get DataJoint tables
        if inspect.isclass(getattr(module, name)) and issubclass(getattr(module, name), dj.Table):
            obj = getattr(module, name)
            for nested in dir(obj):
                # Get Part tables
                if inspect.isclass(getattr(obj, nested)) and issubclass(getattr(obj, nested), dj.Part):
                    setattr(getattr(obj, nested), '_master', obj)


def _create_vm(schema_name:str, external_stores=None, adapter_objects=None):
    """
    Creates a virtual module after registering the external stores, and includes the adapter objects in the vm. 

    Creating tables disabled from virtual modules. 
    """
    
    if external_stores is not None:
        register_externals(external_stores)
    
    return dj.create_virtual_module(schema_name, schema_name, add_objects=adapter_objects, create_tables=False)

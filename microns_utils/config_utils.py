import traceback
import requests
import pkg_resources
import warnings
import re

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

def get_package_version(repo, package, user='cajal', branch='main', source='commit'):
    """
    Gets package version.

    :param repo (str): name of repository
    :param package (str): name of package (contains setup.py) 
    :param user (str): owner of repository
    :param branch (str): branch of repository
    :param source (str): 
        options: 
            "commit" - gets version of latest commit
            "tag" - gets version from latest tag
    :returns: latest version
    """
    # TODO: switch this to git tags
    if source == 'tag':
        pass
    elif source == 'commit':
        f = requests.get(f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/python/version.py")
        latest = ''.join(re.findall("[\d.]", f.text))
    else:
        raise ValueError(f'source: "{source}" not recognized.')
    
    __version__ = [p.version for p in pkg_resources.working_set if p.project_name == package][0]

    if __version__ != latest:
        warnings.warn(f'You are using {package} version {__version__}, which is not the latest version. Version {latest} is available. Consider upgrading to avoid conflicts with the database.')
    
    return __version__
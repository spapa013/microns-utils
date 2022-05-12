"""
Classes and methods for configuring microns packages.
"""
import datajoint_plus as djp

class SchemaConfig:
    """
    DataJoint schema configuration object.
    """
    def __init__(self, module_name:str, schema_name:str, externals:dict=None, adapters:dict=None):
        """
        Initializes DataJoint configuration object.
        
        :param module_name: name of Python module containing DataJoint tables
        :param schema_name: name of DataJoint schema object
        :param externals: dictionary of externals folders to map to schema
        :param adapters: adapters to add to schema context
        """
        self._module_name = module_name
        self._schema_name = schema_name
        self._externals = externals
        self._adapters = adapters
    
    @property
    def module_name(self):
        return self._module_name
    
    @property
    def schema_name(self):
        return self._schema_name
    
    @property
    def externals(self):
        return self._externals
    
    @property
    def adapters(self):
        return self._adapters
    
    def register_externals(self):
        if self.externals is not None:
            djp.register_externals(self.externals)
    
    def register_adapters(self, context=None):
        if self.adapters is not None:
            djp.add_objects(self.adapters, context=context)

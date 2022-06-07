"""
Utils for DataJoint adapters
"""

import datajoint as dj
import numpy as np
import h5py
from pathlib import Path
from collections import namedtuple
import pickle
from datetime import datetime
import logging

from .filepath_utils import validate_filepath


class Adapter(dj.AttributeAdapter):
    attribute_type = ''

    def __init__(self, attribute_type):
        self.attribute_type = attribute_type
        super().__init__()


class FilePathAdapter(Adapter):    
    def put(self, filepath):
        return validate_filepath(filepath)

    def get(self, filepath):
        return validate_filepath(filepath)


class PickleAdapter(Adapter):
    def put(self, object):
        return pickle.dumps(object)

    def get(self, pickled):
        return pickle.loads(pickled)


class MeshAdapter(FilePathAdapter):
    def get(self, filepath):
        filepath = super().get(filepath)
        return adapt_mesh_hdf5(filepath, filepath_has_timestamp=True)


class NumpyAdapter(FilePathAdapter):
    def get(self, filepath):
        filepath = super().get(filepath)
        return np.load(filepath, mmap_mode='r')

def adapt_mesh_hdf5(filepath, parse_filepath_stem=True, filepath_has_timestamp=False, separator='__', timestamp_fmt="%Y-%m-%d_%H:%M:%S", return_type='namedtuple', as_lengths=False):
    """
    Reads from a mesh hdf5 and returns vertices, faces and additional information in the form of a namedtuple or optionally
        as a dictionary, or optionally as separate variables.
        
    :param filepath: File path pointing to the hdf5 mesh file. 
    :param parse_filepath_stem: (bool) 
        If True: Attempts to parse filepath stem
        If False: Skips parsing of filepath stem
    :param filepath_has_timestamp: (bool) Toggles format of expected filename stem to parse.
        If True: expects format '<segment_id><separator><timestamp>'.h5
        If False: expects format '<segment_id>'.h5
    :param timestamp_separator: (str) 
    :param timestamp_fmt:
    :param return_type: Options = {
        namedtuple = return a namedtuple with the following fields {
            vertices = vertex array
            faces = face array
            segment_id = segment id of mesh if parsed else np.nan
            timestamp = timestamp mesh was computed if parsed else ''
            filepath = filepath of mesh
        }
        dict = return a dictionary with keys as in namedtuple
        separate: returns separate variables in the following order {
            vertex array 
            face array
            dictionary with keys segment_id, timestamp, filepath as in namedtuple
            }
    :param as_lengths: Overrides return_type and instead returns:
            Length of the vertex array
            Length of face array
            dictionary with keys segment_id, timestamp, filepath as in namedtuple
        This is done without pulling the mesh into memory, which makes it far more space and time efficient.
    }
    """
    Mesh = namedtuple('Mesh', ['vertices', 'faces', 'segment_id', 'timestamp', 'filepath'])
    filepath = Path(filepath)
    
    # try to parse filepath
    info_dict = {'filepath': filepath}
    defaults = {'segment_id': np.nan, 'timestamp': ''}
    if parse_filepath_stem:
        try:
            if not filepath_has_timestamp:
                segment_id = filepath.stem
                info_dict.update({**{'segment_id': int(segment_id), 'timestamp': ''}})
            else:
                segment_id, timestamp = filepath.stem.split(separator)
                timestamp = datetime.strptime(timestamp, timestamp_fmt)
                info_dict.update({**{'segment_id': int(segment_id), 'timestamp': timestamp}})
        except:
            info_dict.update({**defaults})
            logging.warning('Could not parse mesh filepath.')
    else:
        info_dict.update({**defaults})

    # Load the mesh data
    with h5py.File(filepath, 'r') as f:
        if as_lengths:
            n_vertices = f['vertices'].shape[0]
            n_faces = int(f['faces'].shape[0] / 3)
            return n_vertices, n_faces, info_dict
        
        vertices = f['vertices'][()].astype(np.float64)
        faces = f['faces'][()].reshape(-1, 3).astype(np.uint32)
    
    # Return options
    return_dict = dict(
                vertices=vertices,
                faces=faces,
                **info_dict
                )
    if return_type == 'namedtuple':
        return Mesh(**return_dict)
    elif return_type == 'dict':
        return return_dict
    elif return_type == 'separate':
        return vertices, faces, info_dict
    else:
        raise TypeError(f'return_type does not accept {return_type} argument')
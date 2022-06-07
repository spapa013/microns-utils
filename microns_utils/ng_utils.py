"""
Methods for interacting with Neuroglancer. 

NeuroglancerAnnotationUI (https://github.com/seung-lab/NeuroglancerAnnotationUI)
"""

import numpy as np
import nglui
import pandas as pd
from .ap_utils import set_CAVEclient
from .misc_utils import wrap

client = set_CAVEclient()
default_ng_res = (4,4,40)
default_img_src = client.info.image_source()

def view_arrays_in_neuroglancer(arrays:list, names:list=None, colors:list=None, image_src:str=None, res:tuple=None, view_kws:dict=None):
    """
    Plot arrays in neuroglancer EM space.
    
    :param arrays: Nx3 coordinate arrays in nanometers
        if one array is
    :param names: list of annotation layer names
    :param colors: list of color strings
    :param image_src: (str) - Neuroglancer image source
        default - microns_utils.ng_utils.default_img_src
    :param res: (tuple) - resolution to set Neuroglancer
        default - microns_utils.ng_utils.default_ng_res 
    :param view_kws: (dict) - keywords to pass to Statebuilder

    :returns: HTML Neuroglancer link
    """
    res = default_ng_res if res is None else res
    viewer = nglui.EasyViewer()
    viewer.add_image_layer('em', default_img_src if image_src is None else image_src)
    viewer.set_resolution(res)
    default_view_kws = dict(show_slices=False, layout='3d', orthographic=True, zoom_3d=18221, position=(240640, 207872,  21360))
    sbs = []
    dfs = []
    
    arrays = wrap(arrays)
    
    if names is None:
        names = [f'layer_{i+1}' for i in range(len(arrays))]
    
    if colors is None:
        colors = ["#{:06x}".format(np.random.randint(0, 0xFFFFFF)) for _ in range(len(arrays))]

    for name, array, color in zip(names, arrays, colors):
        dfs.append(pd.DataFrame([[[e[0],e[1],e[2]]] for e in array/res]).rename(columns={0: name}))
        annotation_layer = nglui.statebuilder.AnnotationLayerConfig(name=name, mapping_rules=nglui.statebuilder.PointMapper(name), color=color)
        sbs.append(nglui.statebuilder.StateBuilder([annotation_layer], view_kws=default_view_kws if view_kws is None else view_kws))
    cb = nglui.statebuilder.ChainedStateBuilder(sbs)
    return cb.render_state(dfs, base_state=viewer.state, return_as='html')


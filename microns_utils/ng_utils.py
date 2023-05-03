"""
Methods for interacting with Neuroglancer. 

NeuroglancerAnnotationUI (https://github.com/seung-lab/NeuroglancerAnnotationUI)
"""

import random
import string
import numpy as np
import nglui
from nglui import EasyViewer
import pandas as pd
from .ap_utils import set_CAVEclient
from .misc_utils import wrap, classproperty
from nglui import statebuilder

default_ng_res = (4,4,40)


class NgLinks:
    _client = None

    @classproperty
    def client(cls):
        if cls._client is None:
            cls._client = set_CAVEclient('minnie65_phase3_v1')
        return cls._client
    
    @classproperty
    def em_src(cls):
        return cls.client.info.image_source()

    @classproperty
    def seg_src(cls):
        return cls.client.info.segmentation_source()
    
    @classproperty
    def nuc_src(cls):
        return cls.client.materialize.get_table_metadata('nucleus_detection_v0')['flat_segmentation_source']
    
    @classproperty
    def em_2p_src(cls):
        return 'precomputed://gs://neuroglancer/alex/calcium/minnie/EM_phase3_2p_coords'
    
    @classproperty
    def vess_2p_src(cls):
        return 'precomputed://gs://neuroglancer/alex/calcium/minnie/2pstack_vessels_highres'

    @classproperty
    def nuc_seg_src(cls):
        return 'precomputed://gs://neuroglancer/alex/calcium/minnie/nuc_seg_phase3_2p_coords'
    # image layers
    @classproperty
    def em_layer(cls):
        return statebuilder.ImageLayerConfig(cls.em_src, contrast_controls=True, black=0.35, white=0.7)
    
    @classproperty
    def seg_layer(cls):
        return statebuilder.SegmentationLayerConfig(cls.seg_src,  name='seg')
    
    @classproperty
    def nuc_layer(cls):
        return statebuilder.SegmentationLayerConfig(cls.nuc_src, name='nuclear-seg')


def view_arrays_in_neuroglancer(arrays:list, names:list=None, colors:list=None, res:tuple=None, view_kws:dict=None, set_CAVEclient_kws=None, client=None):
    """
    Plot arrays in neuroglancer EM space.
    
    arrays 
        Nx3 coordinate arrays in nanometers
    names
        list of annotation layer names
    colors
        list of color strings
    res (tuple)
        resolution to set Neuroglancer
        default - microns_utils.ng_utils.default_ng_res 
    view_kws (dict)
        keywords to pass to Statebuilder
    set_CAVEclient (dict) 
        keywords to pass to set_CAVEclient, ignored if client is provided
    client (CAVEclient)
        client to use
    returns
        HTML Neuroglancer link
    """
    client = client if client is not None else set_CAVEclient(**set_CAVEclient_kws if set_CAVEclient_kws is not None else {})
    res = default_ng_res if res is None else res
    viewer = nglui.EasyViewer()
    viewer.add_image_layer('em', client.info.image_source())
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


def custom_viewer(image_kws:dict=None, seg_kws:dict=None, res:tuple=None, add_em_contrast_shader=True, view_options_kws=None, set_CAVEclient_kws=None, client=None):
    """
    image_kws (dict)
        kws to pass to add_image_layer
        default - None
    seg_src (str)
        Neuroglancer segmentation source
        default - microns_utils.ng_utils.default_seg_src
    seg_src (str)
        kws to pass to add_segmentation_layer
        default - None
    res (tuple)
        resolution to set Neuroglancer
        default - microns_utils.ng_utils.default_ng_res
    add_em_contrast_shader (bool)
        adds contrast shader controls to EM layer
        default - True
    set_CAVEclient (dict) 
        keywords to pass to set_CAVEclient, ignored if client is provided
    client (CAVEclient)
        client to use
    returns
        EasyViewer
    """
    client = client if client is not None else set_CAVEclient(**set_CAVEclient_kws if set_CAVEclient_kws is not None else {})
    viewer = EasyViewer()
    # set em layer
    image_kws = {} if image_kws is None else image_kws
    viewer.add_image_layer(
        layer_name='em', 
        source=client.info.image_source(), 
        **image_kws
    )
    if add_em_contrast_shader:
        viewer.add_contrast_shader('em')
    # set seg layer
    seg_kws = {} if seg_kws is None else seg_kws
    viewer.add_segmentation_layer(
        layer_name='seg', 
        source=client.info.segmentation_source(),
        **seg_kws)
    # set ng resolution
    viewer.set_resolution(default_ng_res if res is None else res)
    # set view options
    view_options_kws = {} if view_options_kws is None else view_options_kws
    view_options_kws.setdefault('show_slices', False)
    view_options_kws.setdefault('layout', 'xy-3d')
    viewer.set_view_options(**view_options_kws)
    return viewer


def generate_random_alphanumeric_string(k=40):
    """
    Returns random alphanumeric string with len k
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k))


def add_point_annotations(annotations:list, annotation_layer_kws=None, view_options_kws=None, viewer:EasyViewer=None, client=None):
    """
    annotations (list)
        list of one or more annotations to add to new annotation layer
    annotation_layer_kws (str)
        kws to pass to add_annotation_layer method
        default - None
    view_options_kws (dict)
        kws to pass to EasyViewer set_view_options method
        default - None
    viewer (nglui EasyViewer)
        base viewer to build on
        default - microns_utils.ng_utils.custom_viewer()
    client (caveclient CAVEclient)
        client to pass to custom_viewer
    returns
        EasyViewer
    """
    viewer = custom_viewer(client=client) if viewer is None else viewer
    
    if isinstance(annotations, np.ndarray):
        annotations = annotations.tolist()

    annotations = wrap(annotations)
    annotation_layer_kws = {} if annotation_layer_kws is None else annotation_layer_kws
    annotation_layer_kws.setdefault('layer_name', 'annotations')
    viewer.add_annotation_layer(**annotation_layer_kws)
    viewer.add_annotations(annotation_layer_kws.get('layer_name'),     [
        {
          "point": anno,
          "type": "point",
          "id": generate_random_alphanumeric_string() # dummy ID
        } for anno in annotations]
    )
    # set view options
    view_options_kws = {} if view_options_kws is None else view_options_kws
    viewer.set_view_options(**view_options_kws)
    return viewer


def view_segments_in_neuroglancer(segments:list, colors:list=None, seg_layer_name='seg', view_options_kws:dict=None, viewer:EasyViewer=None, client=None):
    """
    Plot segments in neuroglancer EM space.
    
    segments (int or list)
        single segment_id or list of segment_id's
    colors (str or list)
        color names or hex codes, e.g. "red", "blue", "#FF0000" 
        default - None
    seg_layer_name (str)
        name to give segmentation layer
        default - "seg"
    view_options_kws (dict)
        kws to pass to EasyViewer set_view_options method
        default - None
    viewer (nglui EasyViewer)
        base viewer to build on
        default - microns_utils.ng_utils.custom_viewer()
    client (caveclient CAVEclient)
        client to pass to custom_viewer
    returns
        EasyViewer
    """
    viewer = custom_viewer(client=client) if viewer is None else viewer
    # add segments
    if isinstance(segments, np.ndarray):
        segments = segments.tolist()
    segs, colors = wrap(segments), wrap(colors)
    viewer.add_selected_objects(
        seg_layer_name, segs, colors=colors
    )
    # set view options
    view_options_kws = {} if view_options_kws is None else view_options_kws
    view_options_kws.setdefault('layout', '3d')
    if len(segments) > 1:
        view_options_kws.setdefault('zoom_3d', 8192)
    else:
        view_options_kws.setdefault('zoom_3d', 2048)
    viewer.set_view_options(**view_options_kws)
    return viewer


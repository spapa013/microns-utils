"""
Methods for interacting with packages from Allen Institute and Seung lab from Princeton. 

CloudVolume (https://pypi.org/project/cloud-volume/)
CAVE (https://pypi.org/project/caveclient/)
NeuroglancerAnnotationUI (https://github.com/seung-lab/NeuroglancerAnnotationUI)
"""

import logging
from datajoint_plus.utils import wrap
from cloudvolume import CloudVolume
from caveclient import CAVEclient
from .misc_utils import classproperty

logger = logging.getLogger(__name__)

m65_public = 'minnie65_public_v343'
m65_internal = 'minnie65_phase3_v1'
m35_public = 'minnie35_public_v0'
m35_internal = 'minnie35_phase3_v0'

def set_CAVEclient(datastack='m65_public', ver=None, caveclient_kws=None):
    """
    Sets CAVE client

    :param datastack: datastack to initialize client with
        Options:
            - "m65_public" (default) -> microns_utils.ap_utils.m65_public
            - "m65_internal" -> microns_utils.ap_utils.m65_internal
            - "m35_public" -> microns_utils.ap_utils.m35_public
            - "m35_internal" -> microns_utils.ap_utils.m35_internal
            - None -> instantiates without datastack
    :param ver: materialization version to set
        default (None) -> latest version

    :param caveclient_kws: kwargs to pass to CAVEclient

    :returns: CAVEclient object
    """
    datastack_mapping = {
        'm65_public': m65_public,
        'm65_internal': m65_internal,
        'm35_public': m35_public,
        'm35_internal': m35_internal
    }

    if datastack in datastack_mapping:
        datastack = datastack_mapping[datastack]
    
    try:
        client = CAVEclient(datastack, **{} if caveclient_kws is None else caveclient_kws)
    except Exception as e:
        if "invalid_token" in e.args[0]:
            logging.error('Valid token not found. Returning unauthorized client.')
            client = CAVEclient()
            client.auth.get_new_token()
            client.info._datastack_name = datastack
            return client
        
        elif "missing_tos" in e.args[0]:
            tos_url = "https://global.daf-apis.com/sticky_auth/api/v1/tos/2/accept"
            logging.error(f'You need to accept the terms of service. Returning unauthorized client.')
            logging.info(f'Terms of service url: {tos_url}')
            print(f'Terms of service url: {tos_url}')
            print('After accepting the TOS, try running again.')
            client = CAVEclient()
            client.info._datastack_name = datastack
            return client

        else:
            logging.exception(e)
            return
            
    if ver is not None:
        try:
            client.materialize._version = int(ver)
        except:
            logging.exception('Could not set materialization version.')
            raise Exception('Could not set materialization version.')

    try:
        logger.info(f'Instantiated CAVE client with datastack "{client.info.datastack_name}" and version: {client.materialize.version}. Most recent version: {client.materialize.most_recent_version()}')
    except:
        logger.info(f'Instantiated CAVE client with datastack "{client.info.datastack_name}"')
   
    return client


class CAVEClient:
    _client = None

    @classproperty
    def client_ver(cls):
        return cls.client.materialize.version

    @classmethod
    def set_client(cls, datastack='m65_internal', ver=None, caveclient_kws=None):
        cls._client = set_CAVEclient(
            datastack=datastack,
            ver=ver,
            caveclient_kws=caveclient_kws
        )

    @classproperty
    def client(cls):
        if cls._client is None:
            cls.set_client()
        return cls._client


def get_stats_from_cv_path(cv_path, mip=None):
    """
    Given a cloudvolume path and optional mip (default = all), returns a dict with the following stats from cloudvolume:
        - res: resolution
        - min_pt: min pt of bounding box in voxels
        - max_pt: max pt of bounding box in voxels
        - ctr_pt: center of bounding box in voxels
        - voxel_offset
    
    :param cv_path (str): CloudVolume path
    :param mip (int): the mip to get stats for. default is None.

    :returns: 
        - If mip=None, list of dictionaries for all mips.
        - If mip is specified, dictionaries with stats.  
    """
    def get_stats_for_mip(mip):
        res = cv.mip_resolution(mip)
        min_pt = cv.mip_bounds(mip).minpt
        max_pt = cv.mip_bounds(mip).maxpt
        ctr_pt = ((max_pt - min_pt) / 2) + min_pt
        voxel_offset = cv.mip_voxel_offset(mip)

        return {
                'mip' : mip,
                'res' : res,
                'min_pt' : min_pt,
                'max_pt' : max_pt,
                'ctr_pt' : ctr_pt,
                'voxel_offset' : voxel_offset
            }

    cv = CloudVolume(cv_path, use_https=True, progress=True)

    return get_stats_for_mip(mip) if mip is not None else [get_stats_for_mip(mip) for mip in list(cv.available_mips)]


def get_stack_from_cv_path(cv_path, mip, seg_ids=None):
    """
    Given a cloudvolume path and mip returns the data stack from cloudvolume.

    :param cv_path (str): CloudVolume path
    :param mip (int): the mip to get stack for
    :param seg_ids (int): optional, the seg_ids to restrict to

    :returns: data stack
    """
    cv = CloudVolume(cv_path, use_https=True, progress=True, fill_missing=True, mip=mip)
    return cv.download(bbox=cv.bounds, segids=None if seg_ids is None else wrap(seg_ids)).squeeze()


def query_nucleus_id_in_CAVE(nucleus_id, table_name=None, set_CAVEclient_kws=None, client=None):
    """
    Queries nucleus_detection_v0 or user provided table in CAVE with the given nucleus_id

    :param nucleus_id (int): nucleus_id to query
    :param table_name (str): table in CAVE to query
        default is nucleus_detection_v0
    :param set_CAVEclient (dict): - keywords to pass to set_CAVEclient
        ignored if client is provided
    :param client (CAVEclient): client to use for the query
    """
    if (set_CAVEclient_kws is not None) and (client is not None):
        logger.warning('when both set_CAVEclient_kws and client are passed set_CAVEclient_kws will be ignored')
    client = client if client is not None else set_CAVEclient(**set_CAVEclient_kws if set_CAVEclient_kws is not None else {})
    df = client.materialize.query_table('nucleus_detection_v0' if table_name is None else table_name, filter_equal_dict={'id': nucleus_id}).rename(columns={'id': 'nucleus_id', 'pt_root_id': 'segment_id'})
    return df


def query_segment_id_in_CAVE(segment_id, table_name=None, set_CAVEclient_kws=None, client=None):
    """
    Queries nucleus_detection_v0 or user provided table in CAVE with the given segment_id

    :param segment_id (int): segment_id to query
    :param table_name (str): table in CAVE to query
        default is nucleus_detection_v0
    :param set_CAVEclient (dict): - keywords to pass to set_CAVEclient
        ignored if client is provided
    :param client (CAVEclient): client to use for the query
    """
    if (set_CAVEclient_kws is not None) and (client is not None):
        logger.warning('when both set_CAVEclient_kws and client are passed set_CAVEclient_kws will be ignored')
    client = client if client is not None else set_CAVEclient(**set_CAVEclient_kws if set_CAVEclient_kws is not None else {})
    df = client.materialize.query_table('nucleus_detection_v0' if table_name is None else table_name, filter_equal_dict={'pt_root_id': segment_id}).rename(columns={'id': 'nucleus_id', 'pt_root_id': 'segment_id'})
    return df
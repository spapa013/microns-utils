"""
Methods for interacting with packages from Allen Institute and Seung lab from Princeton. 

CloudVolume (https://pypi.org/project/cloud-volume/)
CAVE (https://pypi.org/project/caveclient/)
"""

import logging
from cloudvolume import CloudVolume
from caveclient import CAVEclient

logger = logging.getLogger(__name__)

def set_CAVE_client(datastack, ver=None):
    client = CAVEclient(datastack)
    
    if ver is not None:
        client.materialize._version = int(ver)

    logger.info(f'Instantiated CAVE client with version: {client.materialize.version}. Most recent version: {client.materialize.most_recent_version()}')
    
    return client


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

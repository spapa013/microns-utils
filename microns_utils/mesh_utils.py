"""Mesh utilities."""

import numpy as np

def index_unique_rows(full_coordinate_array):
    """
    Separates an array of nested coordinate rows into an array of unique rows and and index array.
    """
    vertices, flat_idx = np.unique(full_coordinate_array.reshape(-1, full_coordinate_array.shape[-1]), axis=0, return_inverse=True)
    return vertices, flat_idx.reshape(-1, full_coordinate_array.shape[-2])

def get_midpoints(edges):
    return (edges[:, 0] + edges[:, 1]) / 2

def get_thresholded_bbox(vertices, threshold):
     return np.array((vertices.min(0), vertices.max(0))) + np.array((-threshold, threshold))[:, None] 

def bbox_point_containment(points, bbox):
    """
    Returns a mask of which points are within the boundary described by the bbox at all.
    """
    return np.logical_and.reduce((
        points[..., 0] >= bbox[0, 0],
        points[..., 0] <= bbox[1, 0],
        points[..., 1] >= bbox[0, 1],
        points[..., 1] <= bbox[1, 1],
        points[..., 2] >= bbox[0, 2],
        points[..., 2] <= bbox[1, 2],
    ), axis=0)



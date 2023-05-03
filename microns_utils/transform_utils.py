"""
Utilities for transformations, adjustments, and registrations of MICrONS volumes.
"""

import numpy as np
from scipy.stats import gaussian_kde
from .misc_utils import wrap


def format_coords(coords_xyz, return_dim=1):
    # format coordinates 
    coords_xyz = np.array(coords_xyz)
    
    assert return_dim == 1 or return_dim == 2, "return_dim must be 1 or 2"
    assert coords_xyz.ndim == 1 or coords_xyz.ndim == 2, 'coords_xyz.ndim must be 1 or 2'
    assert coords_xyz.shape[-1] == 3, 'coords_xyz must have 3 columns'
    
    coords_xyz = coords_xyz if coords_xyz.ndim == return_dim else np.expand_dims(coords_xyz, 0)
        
    return coords_xyz


def normalize(points, points_min, points_max, new_min, new_max):
    """
    Normalize arrays to new values.
    """
    return (points - points_min) * ((new_max - new_min) / (points_max - points_min)) + new_min


def normalize_image(image, newrange=[0, 255], clip_bounds=None, astype=np.uint8):
    image = np.array(image)
    if clip_bounds is not None:
        image = np.clip(image,clip_bounds[0], clip_bounds[1]) 
    return (((image - image.min())*(newrange[1]-newrange[0])/(image.max() - image.min())) + newrange[0]).astype(astype)


def run_kde(data, nbins, bounds='auto', method='gaussian_kde', method_kws=None):
    """
    Generate kernel density estimation from data
    
    data : array_like
        1-D data to estimate kde from
    nbins : int
        number of bins for auto-generated grid to evaluate kde pdf generated from data
    bounds : str or tuple 
        Min, Max bounds of auto-generated grid to evaluate kde pdf 
        Options :
            "auto" - (default) min and max computed from data
            tuple - (min, max)
    method : str
        kde method to use
        Options :
            "gaussian_kde" : scipy.stats.gaussian_kde
    method_kws : dict
        kws to pass to kde method
    Returns
        grid, kde pdf evaluated over grid
    """
    method_options = ['gaussian_kde']
    method_kws = {} if method_kws is None else method_kws
    if bounds == 'auto':
        min_bound = data.min()
        max_bound = data.max()
    else:
        min_bound, max_bound = bounds
    grid = np.linspace(min_bound, max_bound, nbins)
    if method in method_options:
        if method == 'gaussian_kde':
            kde = gaussian_kde(data, **method_kws)
            return grid, kde.pdf(grid).reshape(grid.shape)
    else:
        raise AttributeError(f'method {method} not supported. Options are {method_options}')
    

def make_grid(bounds, axis=None, *, npts=None, step=None, clip_bounds_dict=None, clip_bounds_method=None):
    """
    Generate a grid from a bounding box. 

    Args:
        bounds (2xN array)
            array with rows of mins and maxs:
                [mins, 
                 maxs]
        axis (None or int or tuple of ints)
            axis or axes for which to generate bounds, e.g: 1 or (0, 2). 
            The default None will return a grid for all axes of the bounding box.
        npts (None or int or tuple of ints, optional)
            The number of grid points for each axis. Use if desired grid bounds must be exact.
            If int is provided, it will be applied to all axes.
        step (None or int or tuple of ints, optional)
            The grid step size for each dimension. Use if desired grid spacing must be exact.
            If int is provided, it will be applied to all axes.
        clip_bounds_dict (None or dict, optional)
            dictionary indexed by axis with tuples of (new_min, new_max). E.g. :
                If clip_bounds_method = "absolute", then new_min and new_max should be the 
                    desired min and max value. If the original min or max is 
                    desired then the str 'min' or 'max' can be used:
                        clip_bounds_dict = {0: (10, 'max')} 
                        This would clip the grid from 10 to the original max in axis 0 
                        but ignore the other axes. 
                If clip_bounds_method = "fraction", then a tuple of fractions can be provided:
                        clip_bounds_dict = {0: (0, 0.5)} 
                        clip_bounds_dict = {2: ('min', 0.5)}
                        clip_bounds_dict = {0: (0.3, 'max'), 1: (-0.5, 1.5)}
        clip_bounds_method (None or str, optional)
            method for clipping bounds. Must be one of:
                - absolute (default)
                - fraction

    Returns:
        grid (ndarray)
    """
    assert (step is not None) ^ (
        npts is not None), 'Provide step or npts'
    bb = np.array(bounds)
    bb_dict = {}
    if axis is not None:
        # make iterable given int, list, tuple or ndarray
        axis = wrap(np.array(axis).tolist())
        assert np.ndim(axis) == 1, 'axis ndim must not be > 1'
        for a in axis:
            bb_dict[a] = bb.T[a]
    else:
        for i, b in enumerate(bb.T):
            bb_dict[i] = b

    if clip_bounds_dict is not None:
        clip_bounds_method = 'absolute' if clip_bounds_method is None else clip_bounds_method
        for a in clip_bounds_dict.keys():
            # split bounding box
            og_min, og_max = bb_dict[a]
            new_min, new_max = clip_bounds_dict[a]
            # update bounds
            if clip_bounds_method == 'absolute':
                bb_min = og_min if new_min == 'min' else new_min
                bb_max = og_max if new_max == 'max' else new_max
            elif clip_bounds_method == 'fraction':
                bb_min = og_min if new_min == 'min' else new_min * \
                    (og_max - og_min) + og_min
                bb_max = og_max if new_max == 'max' else new_max * \
                    (og_max - og_min) + og_min
            else:
                raise AttributeError(
                    f'clip_bounds_method "{clip_bounds_method}" invalid')
            # reconstitute bounding box
            bb_dict[a] = np.array([bb_min, bb_max])
    if npts is not None:
        if np.ndim(npts) == 0:
            npts = np.repeat(npts, len(bb_dict.keys()))
        meshgrid_args = [np.linspace(*bb_dict[a], num=npts[i])
                         for i, a in enumerate(bb_dict.keys())]
    if step is not None:
        if np.ndim(step) == 0:
            step = np.repeat(step, len(bb_dict.keys()))
        meshgrid_args = [np.arange(*bb_dict[a], step=step[i])
                         for i, a in enumerate(bb_dict.keys())]
    return np.stack(
        np.meshgrid(
            *meshgrid_args,
            indexing='ij'
        ),
        axis=-1
    )


def rotate_points_3d(points, cols, degrees, decimals=3):
    """  
    Rotates about one or more columns of an Nx3 array

    points: Nx3 numpy array
        points to rotate
    cols: int or tuple
        column to rotate about. 
            cols = 1 is equivalent to rotating the array about cols[:, 1]
            cols = (0, 2) is equivalent to rotating first about cols[:, 0] and then about cols[:, 2]
    degrees: int or tuple
        degrees to rotate. should match len of cols
    decimals: int
        the number of decimals to pass to np.round 

    returns: Nx3 numpy array (float)
        rotated points
    """
    points = np.array(points)
    assert points.ndim == 2 and points.shape[1] == 3, 'points must be Nx3'
    # make iterable given int, list, tuple or ndarray
    cols = wrap(np.array(cols).tolist())
    angles = wrap((np.array(degrees) * np.pi / 180).tolist())
    assert len(cols) == len(angles), 'cols and degrees must be the same len'

    def rotate0(points, angle):
        rotated = points.copy().astype(float)
        rotated[..., 1] = points[..., 1] * \
            np.cos(angle) - points[..., 2] * np.sin(angle)
        rotated[..., 2] = points[..., 1] * \
            np.sin(angle) + points[..., 2] * np.cos(angle)
        return rotated.round(decimals=decimals)

    def rotate1(points, angle):
        rotated = points.copy().astype(float)
        rotated[..., 0] = points[..., 0] * \
            np.cos(angle) + points[..., 2] * np.sin(angle)
        rotated[..., 2] = points[..., 2] * \
            np.cos(angle) - points[..., 0] * np.sin(angle)
        return rotated.round(decimals=decimals)

    def rotate2(points, angle):
        rotated = points.copy().astype(float)
        rotated[..., 0] = points[..., 0] * \
            np.cos(angle) - points[..., 1] * np.sin(angle)
        rotated[..., 1] = points[..., 0] * \
            np.sin(angle) + points[..., 1] * np.cos(angle)
        return rotated.round(decimals=decimals)

    for col, angle in zip(cols, angles):
        if col == 0:
            points = rotate0(points, angle)
        if col == 1:
            points = rotate1(points, angle)
        if col == 2:
            points = rotate2(points, angle)
        if col not in (0, 1, 2):
            raise AttributeError(f'column {col} not supported')

    return points
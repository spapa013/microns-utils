"""
Utilities for transformations, adjustments, and registrations of MICrONS volumes.
"""

import numpy as np
from scipy.stats import gaussian_kde

def normalize(points, points_min, points_max, new_min, new_max):
    """
    Normalize arrays to new values.
    """
    return (points - points_min) * ((new_max - new_min) / (points_max - points_min)) + new_min


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
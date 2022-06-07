"""
Utilities for transformations, adjustments, and registrations of MICrONS volumes.
"""

import numpy as np


def normalize(points, points_min, points_max, new_min, new_max):
    """
    Normalize arrays to new values.
    """
    return (points - points_min) * ((new_max - new_min) / (points_max - points_min)) + new_min
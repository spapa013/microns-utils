import numpy as np
from sklearn.cluster import DBSCAN


def cluster_point_cloud(points, eps=5000, min_samples=2, algorithm='auto', return_indices=False):
    """
    Cluster a point cloud using DBSCAN algorithm.

    Parameters:
    - points: An Nx3 array of points.
    - eps: The maximum distance between two samples for one to be considered as in the neighborhood of the other.
    - min_samples: The number of samples (or total weight) in a neighborhood for a point to be considered as a core point. This includes the point itself.
    - return_indices: Whether to return the indices of the points in each cluster.

    Returns:
    - clusters: A list of clusters, where each cluster is a numpy array of shape Mx3, and M is the number of points in the cluster.
    - cluster_indices: A list of clusters, where each cluster is a numpy array of shape M, and M is the number of points in the cluster. Only returned if return_indices is True.
    """
    # Fit DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples, algorithm=algorithm).fit(points)
    
    # Get labels
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    # Create clusters
    clusters = [points[labels == i] for i in range(n_clusters)]
    
    if return_indices:
        cluster_indices = [np.where(labels == i)[0] for i in range(n_clusters)]
        return clusters, cluster_indices
    else:
        return clusters
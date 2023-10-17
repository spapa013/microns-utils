import numpy as np

def plot_cube_edges_3D(ax, origin, size=1, c='k', alpha=1):
    """
    Plots the edges of a 3D cube on the given matplotlib axis 'ax'. 
    
    Parameters:
        ax : matplotlib axis
            The axis on which the cube edges will be plotted.
        origin : list or tuple
            The bottom left front corner of the cube.
        size : float
            The side length of the cube.
    """
    # Define the vertices of the unit cube
    vertices = np.array([[0, 0, 0],
                         [0, 1, 0],
                         [1, 1, 0],
                         [1, 0, 0],
                         [0, 0, 1],
                         [0, 1, 1],
                         [1, 1, 1],
                         [1, 0, 1]])
    vertices = vertices * size + origin
    
    # List of sides' pairs of the cube
    edges = [[0, 1], [1, 2], [2, 3], [3, 0], [0, 4], [1, 5], [2, 6], [3, 7], [4, 5], [5, 6], [6, 7], [7, 4]]
    
    # Plot the edges
    for edge in edges:
        line = np.array([vertices[edge[0]], vertices[edge[1]]])
        ax.plot(line[:, 0], line[:, 1], line[:, 2], c=c, alpha=alpha)
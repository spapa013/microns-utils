"""
Utilities for modeling.
"""
import numpy as np
from functools import reduce
import re
from scipy.interpolate import griddata, RBFInterpolator

class InterpModel:
    def __init__(self, points, values, method, method_kws={}):
        """
        Initialize with parameters for supported interpolation methods.

        :param points: (N x F array) N samples x F features
        :param values: (N x T array) N samples x T targets
        :param method: (str) Interpolation function to initialize.
            Options: 
                - "griddata" - scipy.interpolate.griddata
                - 'rbf' - scipy.interpolate.RBFInterpolator
        :param method_kws: (dict) keywords to pass to interpolation function

        To use, pass points to interpolate to run() after initialization
        """
        valid_methods = ['griddata', 'rbf']
        assert method in valid_methods, f'Method provided not recognized. Valid methods: {valid_methods}'

        self._points = points
        self._values = values
        self._method = method
        self.method_kws = method_kws
    
    @property
    def points(self):
        return self._points

    @property
    def values(self):
        return self._values

    @property
    def method(self):
        return self._method

    def run(self, xi):
        """
        :param xi: Points at which to interpolate data
        
        :returns: array of interpolated values.
        """
        if self.method == 'griddata':
            return griddata(self.points, self.values, xi, **self.method_kws)
        
        if self.method == 'rbf':
            return RBFInterpolator(self.points, self.values, **self.method_kws)(xi)
        
        raise AttributeError(f'method {self.method} not recognized.')
    
    
class PolyModel:
    def __init__(self, features, targets, model):
        """
        Solve for the constants of a polynomial model given a set of features and targets.

        :param features: (N x F array) N is the number of samples and F is the number of features
        :param targets: (N x T array) N is the number of samples and T is the number of targets
        :param model: (str) the polynomial model to fit with F numbers of variables. A bias term is automatically included.
        
        The model is fit using least squares with the formula:
            
            inv(X.T @ X) @ (X.T @ Y)

        Solve a linear model:
        
            Start with a (3 x 2) feature array, i.e. 3 data points each with 2 features.

                features = 
                    [            
                        [4, 2],
                        [8, 2],
                        [9, 1]
                    ]

            Set targets to a (3 x 1) array, i.e. 3 data points with 1 target:

                targets = 
                [
                    [1],
                    [4],
                    [7]
                ]

            Pass model as a str with a unique variable for every feature dimension. The variables can be any [a-z] character.
            
            features is (3 x 2), therefore 2 variables are needed. 

                model = "x + y"

            Upon initialization, three constants will be computed:
                The value of the bias term
                The value of the constant for the x term
                The value of the constant for the y term
            
            Solve model:
                
                m = PolyModel(features, targets, model)

            To view the computed constants. The bias term is always the first constant.

                m.constants

                > array([[ 2.5 ],
                >        [ 0.75],
                >        [-2.25]])

            To view the R^2 value:

                m.r2

                > array([1.])
                
        A quadratic model could take the following form:

            model = "x + y + x*y + x^2 + y^2"

        If features had 3 dimensions (N x 3), the model would need to have 3 unique variables. 

            For example, this model defines x, y, and z:

                model = "x + y + z + x*y^2 + y^3*z^2"
                
        Multiple models can be solved simultaneously by passing in multiple targets, T. 
        
        Appending an additional column to the target from above gives:
        
        targets = 
                [
                    [1, 8],
                    [4, 6],
                    [7, 5]
                ]
        
        The columns in m.constants and m.r2 maps to the columns in targets.
        
            m.constants
            
                > array([[ 2.5 ,  9.  ],
                >       [ 0.75, -0.5 ],
                >       [-2.25,  0.5 ]])
            
            m.r2
                
                > array([1., 1.])
        """
        assert np.ndim(features) == 2, 'features must be 2 dimensional'
        assert np.ndim(targets) == 2, 'targets must be 2 dimensional'
        self.features = features
        self.targets = targets
        self.model = model
        self._terms = ['_bias'] + [t.strip() for t in model.split('+')]
        self.variables = np.unique(re.findall('[a-z]', model)).tolist()
        self._features_with_bias = np.hstack([np.expand_dims(np.ones(len(self.features)), 1), self.features])
        
        assert len(self.features.T) == len(self.variables), \
            f'The feature dimension must match the number of model variables. features.shape[1] = {self.features.shape[1]}, but the model has {len(self.variables)} variables.'
        
        for ll, ff in zip(['_bias'] + self.variables, self._features_with_bias.T):
            setattr(self, ll, np.expand_dims(ff, 1))
        
        mod_terms = self._terms.copy()
        for ii, tt in enumerate(self._terms):
            mod_terms[ii] = reduce(lambda mm, nn: mm.replace(nn, f'{nn}').replace('^', '**').strip(), ['_bias'] + self.variables, tt)
        
        # solve
        fc = []
        for tt in mod_terms:
            fc.append(eval(tt, self.__dict__.copy()))
        self._features_computed = np.hstack(fc)
        
        self.constants = self.least_squares(self._features_computed, self.targets)
        self.r2 = 1 - (np.sum((self.run(self.features) - self.targets)**2, 0) / np.sum((self.targets - self.targets.mean(0))**2, 0))
        
    @staticmethod
    def least_squares(p, q):
        return np.linalg.inv(p.T @ p) @ (p.T @ q)
    
    def run(self, data):
        """
        Run model with data.
        
        :param data: (N x F array)  N is the number of samples and F is the number of features  
        
        :returns: model output
        """
        assert len(data.T) == len(self.variables), \
            f'The feature dimension must match the number of model variables. data.shape[1] = {data.shape[1]}, but the model has {len(self.variables)} variables.'
        
        mapping = {}
        for var, col in zip(self.variables, data.T):
            mapping[var] = col
        features = [np.expand_dims(np.ones(len(data)), 1)]
        for t in self._terms[1:]:
            features.append(np.expand_dims(eval(t.replace('^', '**'), mapping), 1))
        out = []
        for const in self.constants.T:
            out.append(np.sum(const * np.hstack(features), 1))
        return np.stack(out).T
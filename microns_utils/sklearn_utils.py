import numpy as np
import pandas as pd
from scipy.stats import chi2, t
from sklearn.metrics import log_loss
from .transform_utils import rotate_points_3d
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import get_scorer, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV


class RotationTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, cols=None, degrees=None, decimals=2):
        self.cols = cols
        self.degrees = degrees
        self.decimals = decimals

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return rotate_points_3d(X, cols=self.cols, degrees=self.degrees, decimals=self.decimals)


def plot_confusion_matrix(
    y_true, 
    y_pred, 
    labels, 
    normalize=None, 
    ax=None,
    vmin=None,
    vmax=None,
    rotate_xticks=False,
    annotate=False,
    annotate_value_threshold=None,
    xlabel=None,
    ylabel=None,
    cmap=None
):
    cm = confusion_matrix(y_true, y_pred, labels=labels, normalize=normalize)
    
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(include_values=False, cmap=cmap, ax=ax)
    disp.im_.set_clim(vmin=vmin, vmax=vmax)
    
    
    if annotate:
        # Threshold for displaying values
        annotate_value_threshold = 0 if annotate_value_threshold is None else annotate_value_threshold
        
        # Annotate values above the threshold
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                if cm[i, j] > annotate_value_threshold:
                    ax.text(j, i, f'{cm[i, j]:.2f}', ha="center", va="center", color="white", fontsize=6)

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if rotate_xticks:
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)


def perform_k_fold_logistic_regression(X, y, n_splits=10, shuffle=True, random_state=None, lr_kws=None, use_CV=False):
    """
    Performs K-Fold cross-validation for logistic regression on a given dataset and returns
    comprehensive details about each fold in a dictionary.

    Parameters:
        X (array-like): Feature dataset, where rows represent samples and columns represent features.
        y (array-like): Target variable for supervised learning.
        n_splits (int, optional): Number of folds for the cross-validation. Default is 10.
        shuffle (bool, optional): Whether to shuffle the data before splitting into batches. Default is True.
        random_state (int, optional): Seed used by the random number generator for shuffling the data.
                                     Use an integer for reproducible output across multiple function calls. Default is None.
        lr_kws (dict, optional): Additional keyword arguments to be passed to the LogisticRegression constructor.
                                 Examples include 'solver', 'max_iter', etc. Default is None.
    
    Returns:
        dict: A list of dictionaries for each fold, where each dictionary contains:
            - 'X_train' (array-like): Training features for the fold.
            - 'X_test' (array-like): Testing features for the fold.
            - 'y_train' (array-like): Training target for the fold.
            - 'y_test' (array-like): Testing target for the fold.
            - 'y_pred' (array-like): Predicted target values for the testing set of the fold.
            - 'model' (LogisticRegression): Trained LogisticRegression model for the fold.
    """
    lr_kws = {} if lr_kws is None else lr_kws
    
    # Initialize KFold
    kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)

    fold_results = []
    fold_number = 0
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Initialize the logistic regression model
        if not use_CV:
            model = LogisticRegression(**lr_kws)
        else:
            model = LogisticRegressionCV(**lr_kws)
        
        # Fit the model
        model.fit(X_train, y_train.ravel())
        
        # predict probabilities
        y_proba = model.predict_proba(X_test)

        # Predict on the test set
        y_pred = model.predict(X_test)

        # extract the coefficients
        coef = model.coef_

        # Save all relevant information for the fold
        fold_results.append({
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'y_proba': y_proba,
            'y_pred': y_pred,
            'coef': coef,
            'model': model
        })
        fold_number += 1

    return fold_results


def likelihood_ratio_test(prob_full, prob_reduced, coef_full, coef_reduced, y_true):
    """
    Performs a likelihood ratio test given the probabilities from the full and reduced models,
    their coefficients, and the true labels. This function calculates the negative log loss for each model
    and uses it to compute the likelihood ratio test statistic.

    Args:
    prob_full: Probabilities from the full model (numpy array of shape [n_samples, n_classes]).
    prob_reduced: Probabilities from the reduced model (numpy array of shape [n_samples, n_classes]).
    coef_full: Coefficient matrix of the full model (numpy array).
    coef_reduced: Coefficient matrix of the reduced model (numpy array).
    y_true: True labels (numpy array of shape [n_samples]).

    Returns:
    Dictionary containing:
    - 'log_likelihood_full': Negative total log loss of the full model.
    - 'log_likelihood_reduced': Negative total log loss of the reduced model.
    - 'test_statistic': Likelihood ratio test statistic.
    - 'degrees_of_freedom': Degrees of freedom (difference in the number of parameters).
    - 'p_value': P-value of the test statistic.
    """
    # Calculate the total negative log loss (negative of the average log likelihood)
    log_likelihood_full = -log_loss(y_true, prob_full) * len(y_true)
    log_likelihood_reduced = -log_loss(y_true, prob_reduced) * len(y_true)
    
    # Compute the test statistic
    test_statistic = -2 * (log_likelihood_reduced - log_likelihood_full)
    
    # Degrees of freedom: difference in number of coefficients (parameters)
    df = np.abs(coef_full.size - coef_reduced.size)
    
    # Compute the p-value
    p_value = chi2.sf(test_statistic, df)
    
    return {
        'log_likelihood_full': log_likelihood_full,
        'log_likelihood_reduced': log_likelihood_reduced,
        'test_statistic': test_statistic,
        'degrees_of_freedom': df,
        'p_value': p_value
    }


def likelihood_ratio_test_from_estimator(model_full, model_reduced, X_full, X_reduced, y_true):
    """
    Performs a likelihood ratio test between two logistic regression models from sklearn, 
    each fitted to a different set of features, handling models that are potentially encapsulated within a pipeline.

    This function extracts the required probabilities and coefficients from the given models and then uses 
    `likelihood_ratio_test` function to compute the likelihood ratio test.

    Args:
    model_full: A fitted scikit-learn model or pipeline (the full model with more predictors).
    model_reduced: A fitted scikit-learn model or pipeline (the reduced model with fewer predictors).
    X_full: The feature set used to evaluate the full model (numpy array or similar).
    X_reduced: The feature set used to evaluate the reduced model (numpy array or similar).
    y_true: The true labels corresponding to both feature sets (numpy array or similar).

    Returns:
    A dictionary containing the log likelihoods of both models, the test statistic, degrees of freedom, and p-value.
    """
    # Extract probabilities for both models using their respective feature sets
    prob_full = model_full.predict_proba(X_full)
    prob_reduced = model_reduced.predict_proba(X_reduced)
    
    # Extract coefficients from both models
    coef_full = get_coefficients(model_full)
    coef_reduced = get_coefficients(model_reduced)
    
    # Call the likelihood ratio test function using extracted probabilities and coefficients
    return likelihood_ratio_test(prob_full, prob_reduced, coef_full, coef_reduced, y_true)


# Helper function to extract coefficients from a model or pipeline
def get_coefficients(model):
    if hasattr(model, 'coef_'):
        return model.coef_
    elif 'steps' in dir(model):  # It's a Pipeline
        # Assuming the last step is the estimator
        return model.steps[-1][1].coef_
    else:
        raise ValueError("Model does not have coefficients or is not a standard scikit-learn Pipeline.")


def paired_ttest_5x2cv(estimator1, estimator2, X, y, scoring=None, random_seed=None, X2=None):
    """
    Implements the 5x2cv paired t test proposed
    by Dieterrich (1998)
    to compare the performance of two models.
    Modified to optionally accept a different input for the second model. 

    Parameters
    ----------
    estimator1 : scikit-learn classifier or regressor

    estimator2 : scikit-learn classifier or regressor

    X : {array-like, sparse matrix}, shape = [n_samples, n_features]
        Training vectors, where n_samples is the number of samples and
        n_features is the number of features.

    y : array-like, shape = [n_samples]
        Target values.

    scoring : str, callable, or None (default: None)
        If None (default), uses 'accuracy' for sklearn classifiers
        and 'r2' for sklearn regressors.
        If str, uses a sklearn scoring metric string identifier, for example
        {accuracy, f1, precision, recall, roc_auc} for classifiers,
        {'mean_absolute_error', 'mean_squared_error'/'neg_mean_squared_error',
        'median_absolute_error', 'r2'} for regressors.
        If a callable object or function is provided, it has to be conform with
        sklearn's signature ``scorer(estimator, X, y)``; see
        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.make_scorer.html
        for more information.

    random_seed : int or None (default: None)
        Random seed for creating the test/train splits.

    X2 : {array-like, sparse matrix}, shape = [n_samples, n_features] (default: None)
        Optional feature set for the second model.

    
    Returns:
        float: t-statistic from the test.
        float: Corresponding p-value from the test.
    """
    # Initialize random state
    rng = np.random.RandomState(random_seed)
    
    # Determine the scorer
    if scoring is None:
        if estimator1._estimator_type == "classifier":
            scoring = "accuracy"
        elif estimator1._estimator_type == "regressor":
            scoring = "r2"
        else:
            raise AttributeError("Estimator must be a Classifier or Regressor.")
    if isinstance(scoring, str):
        scorer = get_scorer(scoring)
    else:
        scorer = scoring

    # Initialize variables for calculations
    variance_sum = 0.0
    first_diff = None

    indices = np.arange(X.shape[0])
    
    # Perform 5x2 CV
    for i in range(5):
        randint = rng.randint(low=0, high=32767)
        indices_A, indices_B, y_A, y_B = train_test_split(indices, y, test_size=0.5, random_state=randint)
        X1_A, X1_B = X[indices_A], X[indices_B]
        X2_A, X2_B = (X2[indices_A], X2[indices_B]) if X2 is not None else (X1_A, X1_B)

        score_diff_1 = scorer(estimator1.fit(X1_A, y_A), X1_B, y_B) - scorer(estimator2.fit(X2_A, y_A), X2_B, y_B)
        score_diff_2 = scorer(estimator1.fit(X1_B, y_B), X1_A, y_A) - scorer(estimator2.fit(X2_B, y_B), X2_A, y_A)
        score_mean = (score_diff_1 + score_diff_2) / 2.0
        score_var = (score_diff_1 - score_mean) ** 2 + (score_diff_2 - score_mean) ** 2
        variance_sum += score_var
        if first_diff is None:
            first_diff = score_diff_1

    # Calculate the t-statistic and p-value
    numerator = first_diff
    denominator = np.sqrt(1 / 5.0 * variance_sum)
    t_stat = numerator / denominator
    pvalue = t.sf(np.abs(t_stat), 5) * 2.0

    return float(t_stat), float(pvalue)
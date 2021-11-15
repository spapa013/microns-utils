import requests
from importlib import metadata
import warnings
import re
import os
import sys


def find_all_matching_files(name, path):
    """
    Finds all files matching filename within path.

    :param name (str): file name to search
    :param path (str): path to search within
    :returns (list): returns list of matching paths to filenames or empty list if no matches found. 
    """
    result = []
    for root, _, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def parse_version(text: str):
    """
    Parses the text from version.py and returns the version. 

    :param text (str): the text from the version.py file.
    :returns (str): version
    """
    return ''.join(re.findall("[\d.]", text))


def get_version_from_distributions(package):
    """
    Checks importlib metadata for an installed version of the package. 
    Note: packages installed as editable (i.e. pip install -e) will not be found.

    :param package (str): name of package:
    :returns (list): package version
    """
    return [dist.version for dist in metadata.distributions() if dist.metadata["Name"] == package]


def get_version_from_sys_path(package, path_to_version_file, warn=True):
    """
    Checks sys.path for package and returns version from internal version.py file.
    
    :param package (str): name of package. must match at the end of the path string in sys.path.
    :param path_to_version_file (str): path to version.py file relative to package path in sys.path.
    :param warn (bool): warnings enabled if True
    :return (list): package version
    """
    path = ''.join([p + path_to_version_file for p in sys.path if re.findall(package+'$', p)])
    file = find_all_matching_files('version.py', path)

    if len(file) == 0:
        if warn:
            warnings.warn('No version.py file found.')
        return []

    elif len(file) > 1: 
        if warn:
            warnings.warn('Multiple version.py files found.')
        return []

    else:
        with open(file[0]) as f:
            lines = f.readlines()[0]
        
    return [parse_version(lines)]


def get_package_version(repo, package, user='cajal', branch='main', tag=None, source='commit', url_suffix='python/version.py', warn=True):
    """
    Gets package version.

    :param repo (str): name of repository
    :param package (str): name of package (contains setup.py) 
    :param user (str): owner of repository
    :param branch (str): branch of repository (if source='commit')
    :param tag (str): specifed tag  (if source='tag')
    :param source (str): 
        options: 
            "commit" - gets version of latest commit
            "tag" - gets version from latest tag
    :param url_suffix (str): suffix to append to github url where latest version.py file is located
    :param warn (bool): warnings enabled if True
    :returns (str): current package version
    """
    # get latest version
    if source == 'tag':
        if tag is not None:
            f = requests.get(f"https://raw.githubusercontent.com/{user}/{repo}/{tag}/{url_suffix}")
        else:
            raise ValueError('Provide arg "tag".')
    elif source == 'commit':
        f = requests.get(f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{url_suffix}")        
    else:
        raise ValueError(f'source: "{source}" not recognized.')
    latest = parse_version(f.text)

    # check installed distributions for versions
    dist_version = get_version_from_distributions(package=package)

    if not dist_version:
        # check sys.path for versions
        sys_version = get_version_from_sys_path(package=package, path_to_version_file='/..', warn=warn)
        if not sys_version:
            return ''
        else: 
            __version__ = sys_version[0]
    else:
        __version__ = dist_version[0]

    if __version__ != latest:
        if warn:
            warnings.warn(f'You are using {package} version {__version__}, which is not the latest version. Version {latest} is available. Consider upgrading to avoid conflicts with the database.')
    
    return __version__
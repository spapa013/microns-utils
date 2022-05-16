"""
Methods for checking installed and latest versions of microns packages.
"""

import traceback
import requests
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata
import logging
import re
import sys
import json
from pathlib import Path
from .filepath_utils import find_all_matching_files


def parse_version(text: str):
    """
    Extracts __version__ from raw text if __version__ follows semantic versioning (https://semver.org/).
    
    Also compatible with a direct semantic version input, i.e.: "x.y.z". 
    
    :param text (str): the text containing the version.
    :returns (str): version if parsed successfully else ""
    """
    semver = "^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    version_search = re.search('__version__.*', text)
    text = version_search.group() if version_search is not None else text
    text = text.split('=')[1].strip(' "'" '") if len(text.split('='))>1 else text.strip(' "'" '")
    parsed = re.search(semver, text)
    return parsed.group() if parsed else ""


def check_latest_version_from_github(owner, repo, source, branch='main', path_to_version_file=None, warn=True):
    """
    Checks github for the latest version of package.

    :param owner (str): Owner of repository
    :param repo (str): Name of repository that contains package
    :param source (str): 
        options: 
            "commit" - Gets version of latest commit
            "tag" - Gets version of latest tag
            "release" - Gets version of latest release
    :param branch (str): Branch of repository if source='commit', defaults to 'main'.
    :param path_to_version_file (str): Path to version.py file from top of repo if source = "commit". 
    :param warn (bool): If true, warnings enabled.
    :returns (str): If successful, returns latest version, otherwise returns "".
    """
    latest = ""
    try:
        if source == 'commit':
            assert branch is not None, 'Provide branch if source = "commit".'
            assert path_to_version_file is not None, 'Provide path_to_version_file if source = "commit".'
            f = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path_to_version_file}")
            latest = parse_version(f.text)
            
        elif source == 'tag':
            f = requests.get(f"https://api.github.com/repos/{owner}/{repo}/tags")
            if not f.ok:
                logging.error(f'Could not check Github version because: "{f.reason}".')
                return latest
            latest = parse_version(json.loads(f.text)[0]['name'][1:])
            
        elif source == 'release':
            f = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases")
            if not f.ok:
                logging.error('Could not check Github version because: "{f.reason}".')
                return latest
            latest = parse_version(json.loads(f.text)[0]['tag_name'][1:])
        
        else:
            raise ValueError(f'source: "{source}" not recognized. Options include: "commit", "tag", "release". ')
    except:
        if warn:
            logging.warning('Failed to check latest version from Github.')
            traceback.print_exc()

    return latest


def latest_github_version_checker(owner, repo):
    """
    Returns a function to check latest version from github.

    :param owner (str): Owner of repository
    :param repo (str): Name of repository that contains package
    """
    def inner(source='tag', branch=None, path_to_version_file=None, warn=True):
        """
        :param source (str): 
            options: 
                "commit" - Gets version of latest commit
                "tag" - Gets version of latest tag
                "release" - Gets version of latest release
        :param branch (str): Branch of repository if source='commit', defaults to 'main'.
        :param path_to_version_file (str): Path to version.py file from top of repo if source = "commit". 
        :param warn (bool): If true, warnings enabled.
        :returns (str): If successful, returns latest version, otherwise returns "".
        """
        return check_latest_version_from_github(owner=owner, repo=repo, source=source, branch=branch, path_to_version_file=path_to_version_file, warn=warn) 
    return inner


def check_package_version_from_distributions(package, warn=True):
    """
    Checks importlib metadata for an installed version of the package. 
    Note: packages installed as editable (i.e. pip install -e) will not be found.

    :param package (str): name of package:
    :returns (str):  If successful, returns version, otherwise returns "".
    """
    version = [dist.version for dist in metadata.distributions() if dist.metadata["Name"] == package]
    if not version:
        if warn:
            logging.warning('Package not found in distributions.')
        return ''
    return version[0]


def check_package_version_from_sys_path(package, path_to_version_file, prefix='', warn=True):
    """
    Checks sys.path for package and returns version from internal version.py file.
    
    :param package (str): name of package. must match at the end of the path string in sys.path.
    :param path_to_version_file (str): path to version.py file relative to package path in sys.path.
    :param prefix (str): path to prepend to package
    :param warn (bool): warnings enabled if True
    :return (str): If successful, returns version, otherwise returns "".
    """
    err_base_str = f'Could not get version for package {package} because '

    paths = [Path(p).joinpath(path_to_version_file) for p in sys.path if re.findall(Path(prefix).joinpath(package).as_posix()+'$', p)]
    
    if len(paths)>1:
        if warn:
            logging.warning(err_base_str + f'{len(paths)} paths containing {package} were found in sys.path. Consider adding a prefix for further specification.')
            [print(p) for p in paths]
        return ''
    
    elif len(paths) == 0:
        if warn:
            logging.warning(err_base_str + f'no paths matching {package} were found in sys.path.')
        return ''
    
    else:
        files = find_all_matching_files('version.py', paths[0])

    if len(files) == 0:
        if warn:
            logging.warning(err_base_str + 'no version.py file was found.')
        return ''

    else:
        with open(files[0]) as f:
            lines = f.readlines()[0]
        
    return parse_version(lines)


def check_package_version(package, prefix='', check_if_latest=False, check_if_latest_kwargs={}, warn=True):
    """
    Checks package version.

    :param package (str): name of package (contains setup.py)
    :param prefix (str): path to prepend to package for check_package_version_from_sys_path
    :param check_if_latest (bool): if True, checks if installed version matches latest version on Github 
    :check_if_latest_kwargs (dict): kwargs to pass to :func:`~version_utils.check_latest_version_from_github`
    :param warn (bool): warnings enabled if True
    :returns (str): current package version
    """
    # check installed distributions for versions
    dist_version = check_package_version_from_distributions(package=package, warn=False)

    if not dist_version:
        # check sys.path for versions
        sys_version = check_package_version_from_sys_path(package=package, prefix=prefix, path_to_version_file='..', warn=warn)
        if not sys_version:
            return ''
        else: 
            __version__ = sys_version
    else:
        __version__ = dist_version

    if check_if_latest:
        # check if package version is latest
        latest = check_latest_version_from_github(**check_if_latest_kwargs)

        if __version__ != latest:
            if warn:
                logging.warning(f'You are using {package} version {__version__}, which does not match the latest version on Github, {latest}.')
    
    return __version__
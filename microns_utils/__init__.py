from . import version_utils

__version__ = version_utils.get_package_version(package='microns-utils')

def get_latest_version_from_github():
    return version_utils.get_latest_version_from_github(repo='microns-utils', user='cajal', branch='main', source='commit', path_to_version_file='microns_utils/version.py', tag=None, warn=True)
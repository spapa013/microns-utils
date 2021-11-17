from . import version_utils
from .version import __version__

def get_latest_version_from_github():
    return version_utils.get_latest_version_from_github(repo='microns-utils', owner='cajal', branch='main', source='commit', path_to_version_file='microns_utils/version.py', tag=None, warn=True)
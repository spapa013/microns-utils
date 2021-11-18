from . import version_utils
from .version import __version__

def check_latest_version_from_github(owner='cajal', repo='microns-utils', source='tag', branch=None, path_to_version_file=None, warn=True):
    """
    Wrapper for :func:`~version_utils.check_latest_version_from_github`
    """
    return version_utils.check_latest_version_from_github(owner=owner, repo=repo, source=source, branch=branch, path_to_version_file=path_to_version_file, warn=warn)
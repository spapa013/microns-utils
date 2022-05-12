from . import version_utils
from .version import __version__

check_latest_version_from_github = version_utils.latest_github_version_checker(owner='cajal', repo='microns-utils')
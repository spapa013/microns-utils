from . import version_utils
from .version import __version__
from .logging_utils import configure_logger

configure_logger()

check_latest_version_from_github = version_utils.latest_github_version_checker(owner='cajal', repo='microns-utils')
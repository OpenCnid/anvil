# [ANVIL PATCH] Package identity: anvilcv fork of rendercv v2.7
# Original: __version__ = "2.7", __description__ = "Resume builder for academics..."
import warnings

from anvilcv import __version__

__rendercv_version__ = "2.7"
__description__ = "Developer-native, AI-powered resume engine — a fork of rendercv"

warnings.filterwarnings("ignore")

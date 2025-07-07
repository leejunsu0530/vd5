from sys import version_info
from .modulemanage.module_update import check_and_update
# ------------------------------
from .main.videosmanager import VideosManager
from .main.videos import Videos
from .richtext.my_console import my_console as con
from .newtypes.formatstr import FormatStr

from .richtext import ask_prompt as ask
from .richtext.read_script import print_code

from .newtypes import new_sum

from rich.text import Text
from rich.style import Style

# 파이썬 버전 확인
if not version_info >= (3, 11):
    raise ImportError("Only Python versions 3.11 and above are supported")

# yt-dlp 확인
check_and_update('yt-dlp', "ask")

__all__ = ["VideosManager", "Videos", "con", "FormatStr", "ask", "print_code", "new_sum", "Text", "Style"]

__version__ = "1.0.0.post2"

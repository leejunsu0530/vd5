from typing import Callable, Any, Literal

from rich.console import Group
from rich.table import Table, Column
from rich import box
from rich.style import Style
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress

from .my_console import my_console


def path_styler(path: str) -> str:
    return path.replace("\\", "/").replace("/", "[bold #ff5c00]/[/]")


def group_text_and_progress(
    text: Text = Text("Unknown"),
    border_style: str | Style = "none",
    progress: Progress = None,
) -> Group:
    panel = Panel(text, border_style=border_style)
    return Group(panel, progress)  # type: ignore


def highlight_normal_text(msg: str):
    msg_text = Text.from_ansi(msg)

    # 1. 대괄호 안의 내용을 (대괄호 포함) magenta 색으로 강조
    msg_text.highlight_regex(r"\[[^\]]*\]", style="magenta")
    # 2. 숫자를 cyan 색으로 강조
    msg_text.highlight_regex(r"\d+", style="cyan")
    # 3. 작은따옴표로 둘러싸인 문자열을 lime 색으로 강조
    msg_text.highlight_regex(r"'[^']*'", style="#8aff67")
    # 4. 파일명 또는 파일 경로 형태의 문자를 orange 색으로 강조.
    # 이 정규식은 드라이브 문자, 콜론, 백슬래시로 시작하여,
    # 하나 이상의 디렉터리 이름이 백슬래시로 구분되고, 확장자를 포함한 파일 이름을 매칭합니다.
    msg_text.highlight_regex(
        r'[A-Za-z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]+\.[^\\\/:*?"<>|\r\n]+',
        style="orange1",
    )

    return msg_text


def hightlight_download_text(msg: str):
    msg_text = Text.from_ansi(msg)
    msg_text.highlight_regex(r"\[[^\]]*\]", style="magenta")  # []내부 처리

    # 1. 퍼센트 (예: "4.9%") → 시안색
    msg_text.highlight_regex(r"\b\d+(?:\.\d+)?%", style="cyan")

    # 2. 총 파일 용량 (예: "13.66MiB") → 초록색
    # "of ~" 부분까지 굳이 매칭할 필요가 없다면, 단순히 파일 크기 형태만 찾으면 됩니다.
    msg_text.highlight_regex(r"\b\d+(?:\.\d+)?[KMGTP]?i?B", style="green")

    # 3. 다운로드 속도 (예: "202.01KiB/s") → 노란색
    # 단순히 "KiB/s"까지 포함해서 하이라이트하고 싶다면 아래와 같이 쓰고,
    # '/s'는 제외하고 "202.01KiB"만 강조하고 싶다면 `(?=/s)` 형태의 룩어헤드를 사용하세요.
    msg_text.highlight_regex(r"\b\d+(?:\.\d+)?[KMGTP]?i?B/s", style="orange1")

    # 4. ETA (예: "ETA 00:44") → 빨강
    msg_text.highlight_regex(r"ETA\s+(?:\d{1,2}:\d{2}|Unknown)", style="red")

    # 5. 조각 정보 (예: "(frag 1/44)") → 주황색
    msg_text.highlight_regex(r"\(frag\s+\d+/\d+\)", style="yellow")

    return msg_text


class LoggerForRich:
    def __init__(self, print_info: bool | Literal['only_download'] = False,
                 skip_lang_warning: bool = True,
                 console=None):
        """print_info: 'only_download', false, true. 특정 시간보다 클때 출력 여부는 외부에서 결정"""
        self.print_info = print_info
        self.skip_lang_warning = skip_lang_warning
        self.console = console if console else my_console

    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith("[debug] "):
            pass
        else:
            self.info(msg)

    @staticmethod
    def highlight_text(msg: str):
        if msg.startswith("[download]"):  # dl은 기본 색 그대로
            msg_text = hightlight_download_text(msg)
        else:  # 다운이 아니면
            msg_text = highlight_normal_text(msg)

        return msg_text

    def info(self, msg: str):
        if self.print_info is False:
            return None
        elif self.print_info == "only_download" and not msg.startswith("[download]"):
            return None

        msg_text = self.highlight_text(msg)
        self.console.print(msg_text)

    def warning(self, msg: str):
        if msg.startswith('[youtube:tab] Preferring "ko" translated fields. Note that some metadata extraction may fail or be incorrect.'):
            return None
        msg_text = Text.from_ansi(msg)
        self.console.print(msg_text, style="bright_yellow")

    def error(self, msg):
        msg = Text.from_ansi(msg)
        self.console.print(msg, style="bright_red")


if __name__ == "__main__":
    T = "[download]   4.9% of ~  13.66MiB at  202.01KiB/s ETA 00:44 (frag 1/44)"
    my_console.print(hightlight_download_text(T))

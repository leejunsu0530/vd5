import requests
from packaging import version
import importlib.metadata

from .execute_cmd import execute_cmd_realtime
from ..richtext.ask_prompt import ask_y_or_n

import sys
from typing import Literal, Callable

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


# 좀 더 rich 의존적이게 수정함


def get_current_version(package_name: str) -> tuple[str | None, str]:
    """
    Return:
        (version, message)
    """
    try:
        v = importlib.metadata.version(package_name)
        return v, f"설치된 현재 버전: {v}"
    except importlib.metadata.PackageNotFoundError:
        return None, "패키지를 찾을 수 없습니다."


def get_latest_version_pypi(package_name: str) -> tuple[str | None, str]:
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        latest_version = data["info"]["version"]
        return latest_version, f"최신 {package_name} 버전: {latest_version}"
    else:
        return None, "PyPI에서 데이터를 가져오는 중 오류 발생"


def compare_version(current_version: str, latest_version: str) -> tuple[bool, str]:
    if version.parse(current_version) < version.parse(latest_version):
        return True, "업데이트가 필요합니다."
    else:
        return False, "이미 최신 버전을 사용 중입니다."


def update_module(to_update: str, print_: Callable = print, print_kwargs: dict = None) -> None:
    execute_cmd_realtime(
        f"{sys.executable} -m pip install --upgrade {to_update}", print_, print_kwargs)


def check_and_update(module_name: str, module_name_to_update: str,
                     update: bool | Literal["ask"] = "ask",
                     print_: Callable = print, print_kwargs: dict = None) -> int:
    """에러코드는 0이 성공, 1이 실패,
    update가 'ask'면 프롬프트로 물어봄"""
    if not module_name_to_update:
        module_name_to_update = module_name
    if print_kwargs is None:
        print_kwargs = {}

    print_(f"현재 가상환경: {sys.executable}", **print_kwargs)
    print_(f"모듈 이름: {module_name}", **print_kwargs)

    current_version, message = get_current_version(module_name)
    print_(message, **print_kwargs)
    if not current_version:
        return 1  # 오류로 종료

    latest_version, message = get_latest_version_pypi(module_name)
    print_(message, **print_kwargs)
    if not latest_version:
        return 1

    need_update, message = compare_version(current_version, latest_version)
    print_(message, **print_kwargs)

    if need_update:
        if update == "ask":
            update = ask_y_or_n("모듈을 업데이트하시겠습니까?")

        if update:  # true면
            update_module(module_name_to_update, print_, print_kwargs)
    print()
    return 0


def check_and_update_in_panel(module_name: str, module_name_to_update: str,
                              update: bool | Literal["ask"] = "ask", console: Console = None) -> Literal[1] | Literal[0]:
    if console is None:
        new_console = Console()
    else:
        new_console = console
    lines = []

    def updater(new_line: str) -> None:
        lines.append(new_line)
        panel_text = new_console.highlighter(
            Text("\n".join(lines), style="bold"))
        live.update(Panel(panel_text))  # 클로져 지원되니까 이거 문제 x

    with Live(Panel("시작 중..."), console=new_console, refresh_per_second=4, transient=False) as live:
        if not module_name_to_update:
            module_name_to_update = module_name

        updater(f"현재 가상환경: {sys.executable}")
        updater(f"모듈 이름: {module_name}")

        current_version, message = get_current_version(module_name)
        updater(message)
        if not current_version:
            return 1  # 오류로 종료

        latest_version, message = get_latest_version_pypi(module_name)
        updater(message)
        if not latest_version:
            return 1

        need_update, message = compare_version(current_version, latest_version)
        updater(message)  # 이 아래 질문에서 꺠지기 때문에 별도의 패널로 분리

    lines = []
    if need_update:
        if update == "ask":
            update = ask_y_or_n("모듈을 업데이트하시겠습니까?")

        if update:  # true면
            with Live(Panel("시작 중..."), console=new_console, refresh_per_second=4, transient=False) as live:
                update_module(module_name_to_update, updater)
        print()
    return 0


# if __name__ == '__main__':
# 여기 .임포트라 테스트 안됨
# check_and_update_in_panel(
    # 'yt-dlp', "yt-dlp[default,curl-cffi]", "ask", con)

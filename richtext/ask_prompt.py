import sys
from typing import Any, Literal

from rich.prompt import Prompt
from rich.style import Style


def ask_choice(msg: str, choice: list[Any] | tuple[Any] | None = None, default: Any = None) -> str:
    """default를 안전하게 처리함"""
    str_choice: list[str] | None = [str(c) for c in choice] if choice else None
    default_dict: dict[Literal["default"], str] = {}
    if default is not None:  # 그냥 not 쓰면 0같은거 무시됨
        default_dict["default"] = str(default)

    return Prompt.ask(msg, choices=str_choice, **default_dict)  # type: ignore


def ask_y_or_n(msg: str, default: str = "n") -> bool:
    if ask_choice(msg, ["y", "n"], default) == "y":
        return True
    else:
        return False


def ask_continue(msg: str = "계속할까요?") -> None:
    if not ask_y_or_n(msg):
        sys.exit()


def ask_choice_num(
    msg: str,
    choice: list[Any] | tuple[Any, ...] = (),
    default: int = None,
    styles: list[str | Style] = None,
) -> int:
    """문자열 리스트로 제공하면 번호 매겨서 선택지 제공
    기본 styles = ["red", "blue", "green", "yellow", "magenta", "cyan", "bright_magenta", "bright_cyan"]
    """
    if not styles:
        styles = ["red", "blue", "green", "yellow", "magenta",
                  "cyan", "bright_magenta", "bright_cyan"]
    new_choice: list[str] = [str(c) for c in choice]
    choice_str = "/".join([f"[{styles[idx % len(styles)]}]{idx}: {c}[/]" for idx,
                          c in enumerate(new_choice)])
    choices_num = [str(i)for i in range(len(new_choice))]
    msg = f"{msg} [{choice_str}]"
    if default is not None:
        msg += f" [cyan]({new_choice[default]})[/]"
    answer = int(ask_choice(msg, choices_num, default))
    return answer


if __name__ == "__main__":
    # print(ask_choice_num("안녕하세요", ["a", "b", "c"]))
    # print(ask_choice("hello", [1, 2]))
    print(ask_choice_num("안녕", ["ㅇ", 4, "ㅁ"], 0))

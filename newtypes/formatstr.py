from datetime import datetime
from typing import Callable, Any, ParamSpec
from functools import wraps


class SafeDict(dict):
    def __missing__(self, key) -> str:
        return f'%({key})s'


def dict_formatting(text: str, dict_: dict) -> str:
    """
    Args:
        text: "%(key)s" shaped str
        dict_: dict with keys
    Return: 
        if not keys in dict_, format key name instead
    """
    safedict = SafeDict(dict_)

    return text % safedict


P = ParamSpec("P")


def _try_and_return_str(func: Callable[P, str]) -> Callable[P, str]:
    """성공하면 수정해서, 실패하면 그대로"""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
        try:
            result = func(*args, **kwargs)
            return result
        except (TypeError, ValueError):
            return str(*args)

    return wrapper


class FormatStr:
    @_try_and_return_str
    @staticmethod
    def filename(input_string: str) -> str:
        invalid_to_fullwidth: dict[str, str] = {
            '<': '＜',  # U+FF1C
            '>': '＞',  # U+FF1E
            ':': '：',  # U+FF1A
            '"': '＂',  # U+FF02
            '/': '／',  # U+FF0F
            '\\': '＼',  # U+FF3C
            '|': '｜',  # U+FF5C
            '?': '？',  # U+FF1F
            '*': '＊',  # U+FF0A
        }

        # Replace each invalid character with its fullwidth equivalent
        for char, fullwidth_char in invalid_to_fullwidth.items():
            input_string = input_string.replace(char, fullwidth_char)

        return input_string

    @_try_and_return_str
    @staticmethod
    def number(num: int | str) -> str:
        """4자리마다 ,로 끊음"""
        num = int(num)

        num_str = str(num)[::-1]  # Reverse the string
        grouped = ",".join(num_str[i:i + 4] for i in range(0, len(num_str), 4))
        return grouped[::-1]  # Reverse it back

    @_try_and_return_str
    @staticmethod
    def date(date: int | str, type_: str = "%y.%m.%d") -> str:
        """yyyymmdd("%Y%m%d") -> yy.mm.dd("%y.%m.%d")"""
        date_obj = datetime.strptime(str(date), "%Y%m%d")
        return date_obj.strftime(type_)

    @_try_and_return_str
    @staticmethod
    def time(seconds: float | int | str, return_int: bool = True) -> str:
        seconds = float(seconds)
        minutes, sec = divmod(seconds, 60)  # 초를 분과 초로 변환
        hours, minutes = divmod(minutes, 60)  # 분을 시와 분으로 변환
        if return_int:
            sec = round(sec)
            if hours >= 1:
                # hh:mm:ss.SS
                return f"{int(hours):02}:{int(minutes):02}:{sec:02}"
            else:
                return f"{int(minutes):02}:{sec:02}"  # mm:ss.SS
        else:
            if hours >= 1:
                # hh:mm:ss.SS
                return f"{int(hours):02}:{int(minutes):02}:{sec:05.2f}"
            else:
                return f"{int(minutes):02}:{sec:05.2f}"  # mm:ss.SS

    @staticmethod
    def _format_byte(byte: int | str, round_: int = 4) -> tuple[float, float, float]:
        """mb, gb 튜플 반환"""
        byte = int(byte)
        kb = round(byte / 1024, round_)
        mb = round(byte / (1024 ** 2), round_)
        gb = round(byte / (1024 ** 3), round_)
        return kb, mb, gb

    @_try_and_return_str
    @staticmethod
    def bytes(byte: int | str, round_: int = 2) -> str:
        kb, mb, gb = FormatStr._format_byte(byte, round_)
        if gb >= 1:
            return f"{gb} GiB"
        elif mb >= 1:
            return f"{mb} MiB"
        else:
            return f"{kb} KiB"


if __name__ == '__main__':
    print(FormatStr.number(10000000))
    print(FormatStr.number("10000000000a"))
    print(FormatStr.number(None))  # type: ignore
    print(FormatStr.bytes(100000, 2))

    info_dict = {
        "title": "video1",
        "thumbnails": ["1", 0.5],
        "age_limit": 15
    }
    text_ = dict_formatting(
        "%(title)s, %(thumbnails)s, %(subtitle)s", info_dict)
    print(text_)

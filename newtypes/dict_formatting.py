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


if __name__ == "__main__":
    info_dict = {
        "title": "video1",
        "thumbnails": ["1", 0.5],
        "age_limit": 15
    }
    text_ = dict_formatting(
        "%(title)s, %(thumbnails)s, %(subtitle)s", info_dict)
    print(text_)

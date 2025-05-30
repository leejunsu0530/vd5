import os
from ..newtypes.ydl_types import ChannelInfoDict, PlaylistInfoDict
from .filesave import read_dict_from_json
from typing import cast


def read_json_with_id(id_: str, dir_path: str) -> PlaylistInfoDict | ChannelInfoDict | None:
    for file_name in os.listdir(dir_path):
        file_id = file_name.rsplit(" ", 1)[-1].strip("[]")
        # 파일명을 공백을 기준으로 왼쪽에서 1번 끊고 거기서 [나 ]를 모두 제거 > id나 id__tab꼴.
        if id_ == file_id:
            info_dict = read_dict_from_json(dir_path, file_name)
            if info_dict:
                return cast(PlaylistInfoDict | ChannelInfoDict, info_dict)
    # 못찾으면 return 안되서 for문 안 깨짐
    return None


def find_path_with_id(id_: str, dir_path: str) -> str | None:
    """아마 비디오 무결성 시 사용될듯"""
    for file_name in os.listdir(dir_path):
        file_id = file_name.rsplit(" ", 1)[-1].strip("[]")
        # 파일명을 공백을 기준으로 왼쪽에서 1번 끊고 거기서 [나 ]를 모두 제거 > id나 id__tab꼴.
        if id_ == file_id:
            return f"{dir_path}\\{file_name}"
    return None

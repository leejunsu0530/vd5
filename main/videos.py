from typing import Callable, Literal, Any, Self, cast
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from collections import Counter
from copy import deepcopy
from rich.style import Style
from rich.text import Text
from rich.panel import Panel
from rich.table import Table, Column
from rich import box

from ..filemanage.filesave import read_str_from_file
from ..filemanage.bring_path import CODE_FILE_PATH
from ..newtypes.formatstr import FormatStr, dict_formatting

from ..newtypes.ydl_types import MAJOR_KEYS, ChannelInfoDict, PlaylistInfoDict, VideoInfoDict, EntryInPlaylist
from ..richtext.loggers import Table, path_styler
from ..richtext.my_console import my_console


def bring_key_list(lst: list[dict], key: str) -> list:
    # 얘는 아래에 통합x (기능이 다르니까)
    return [dict_.get(key) for dict_ in lst]


class DictSetOperator:
    """여차하면 이거 내부 클래스로 통합할 수도?"""
    @staticmethod
    def union(list1: list[VideoInfoDict | EntryInPlaylist], list2: list[VideoInfoDict | EntryInPlaylist]) -> list[VideoInfoDict | EntryInPlaylist]:
        """합집합"""
        set1 = {json.dumps(item, sort_keys=True) for item in list1}
        set2 = {json.dumps(item, sort_keys=True) for item in list2}

        # 집합 연산 수행
        sum_json = set1 | set2

        # JSON 문자열을 다시 딕셔너리로 변환
        sum_ = [json.loads(item) for item in sum_json]

        return sum_

    @staticmethod
    def diff(list1: list[VideoInfoDict | EntryInPlaylist], list2: list[VideoInfoDict | EntryInPlaylist]) -> list[VideoInfoDict | EntryInPlaylist]:
        """차집합"""
        set1 = {json.dumps(item, sort_keys=True) for item in list1}
        set2 = {json.dumps(item, sort_keys=True) for item in list2}

        # 집합 연산 수행
        diff_json = set1 - set2

        # JSON 문자열을 다시 딕셔너리로 변환
        difference = [json.loads(item) for item in diff_json]

        return difference

    @staticmethod
    def inter(list1: list[VideoInfoDict | EntryInPlaylist], list2: list[VideoInfoDict | EntryInPlaylist]) -> list[VideoInfoDict | EntryInPlaylist]:
        """교집합"""
        set1 = {json.dumps(item, sort_keys=True) for item in list1}
        set2 = {json.dumps(item, sort_keys=True) for item in list2}

        # 집합 연산 수행
        inter_json = set1 & set2

        # JSON 문자열을 다시 딕셔너리로 변환
        intersection = [json.loads(item) for item in inter_json]

        return intersection


class VideoListsManageMixin:  # 이건 일단 추상화할 필요 x
    """list_all_videos를 관리하고 다른 리스트들로 분류함. 리스트들 정의는 여기서 안하고 자식에서."""

    def _check_attr(self):
        """속성들이 메인에 정의되어 있는지 검사하는 메서드"""

    def update(self):
        # 자신만의 업데이트 동작을 한 후 체인에 연결된 다음 믹스인의 업데이트 실행
        if hasattr(super(), "update"):
            super().update()


class DictListTransformMixin:
    """자르기, 필터링, 사칙연산은 아예 원본과 다른 정보의 객체를 만들어냄. sort는 여기서 정의 안하고, 이 위 믹스인에서 할지 메인에서 할지 고민중"""

    def update(self):
        # 자신만의 업데이트 동작을 한 후 체인에 연결된 다음 믹스인의 업데이트 실행
        if hasattr(super(), "update"):
            super().update()

    # 이제 이 아래에 cut, 필터링, 사칙연산 끌고 와야 하는데, 일단 밑에 정리 좀 하고


@dataclass
class TableKey:
    """표에 사용되는 구체적인 키 설정. alias는 생성하지 않았을 시 자동으로 key로 설정"""
    key: str
    alias: str = ""

    @staticmethod
    def return_str(value) -> str:
        return str(value)
    # 람다 경고 회피. 그리고 직접 정의보다 이게 더 직관적인듯?
    # gpt는 그냥 str(함수니까) 쓰면 된다 하는데, 나중에 내가 햇갈릴거 같아서
    formatter: Callable[..., str] = return_str
    formatter_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.alias == "":
            self.alias = self.key


class VideosTableMixin(ABC):  # 이건 메니져에서도 상속.
    # 기본 표 키 정의
    default_keys_to_show: tuple[TableKey, ...] = (
        TableKey("title"),
        TableKey("upload_date", formatter=FormatStr.date),
        TableKey("view_count", formatter=FormatStr.number),
        TableKey("like_count", formatter=FormatStr.number),
        TableKey("duration", formatter=FormatStr.time),
        TableKey("filesize_approx", formatter=FormatStr.bytes)
    )

    @property
    @abstractmethod
    def videos_list(self) -> list["Videos"]:
        """return [self]같은 식으로 재정의"""

    def print_table(self,
                    # 함수에 인자로 kwargs 들어가서 Callable[Any로는 안됨]
                    *keys: str | tuple[str, Callable[[Any], str]] | TableKey,
                    restrict: Callable[[VideoInfoDict |
                                        EntryInPlaylist], bool] = None,  # 이걸 여기서 적용한 후 그 적용된 딕셔너리 리스트를 제공하는 게 낫겠지. 팔요시 위쪽 계산 함수들도 여기로 이관
                    box_: box.Box | None = box.HEAVY_HEAD,
                    show_lines: bool = False,
                    skow_edge: bool = True,
                    expand: bool = False,
                    no_wrap: bool = False,
                    highlight: bool = False
                    ) -> None:
        """
        테이블을 만드는 건 여기서.

        Args:
            keys: 아래의 형태 중 하나가 들어갈 수 있음
                - 딕셔너리의 키가 되는 문자열
                - (키, 포메팅 함수) 형태의 튜플 (※함수는 하나의 인자만 가능)
                - TableKey 객체. 키, 표시할 키의 이름, 포메팅 함수, 포메팅 함수에 전달할 인자를 설정 가능

        """
        new_keys: list[TableKey] = []
        for key in keys:
            if isinstance(key, str):
                new_keys.append(TableKey(key))
            elif isinstance(key, tuple):
                k, formatter = key
                new_keys.append(TableKey(k, formatter=formatter))
            elif isinstance(key, TableKey):
                new_keys.append(key)
            else:
                raise TypeError(f"지원하지 않는 키 형식({type(k)})입니다: {k}")

        # 각 요소에 대한 정보를 지닌 리스트
        _columns_str: list[str] = ["index"] + [tk.alias for tk in new_keys]
        columns: list[Column] = [
            Column("index", max_width=5, no_wrap=no_wrap)] + [Column(tk.alias, no_wrap=no_wrap) for tk in new_keys]  # 전과는 달리 뒤쪽은 max 지정 안함. 일단은
        # columns에서 일반 색/어두운 색으로 구체화 << 이거 보기에 안좋아서 그냥 box.HEAVY_HEAD로 줄 나눔

        # 만약 비디오스에서 호출한거면 정렬순으로 강조
        if len(self.videos_list) == 1:
            sort_key, sort_reverse = self.videos_list[0].sort_by
            if sort_key in columns:
                idx = _columns_str.index(sort_key)
                arrow = "▼" if sort_reverse else "▲"
                columns[idx] = Column(
                    f"[bold bright_magenta]{columns[idx]}{arrow}[/]")

            # 일단 pl_folder_name을 사용하는 쪽으로 지정.
            title = f"{self.videos_list[0].pl_folder_name} Table"
        else:
            title = "Total Table"

        # 캡션 달기
        caption = ""
        table_infos: list[dict] = []
        for videos in self.videos_list:
            caption += f"{videos.format_table_info()}\n"  # 색은 저쪽에서 자동으로 입혀줌
            table_infos.append(videos.calculate_table_info())
        total_table_info = dict(sum((Counter(i)
                                for i in table_infos), Counter()))
        caption += self.format_table_info(
            total_table_info)

        table = Table(
            *columns,
            title=title,
            caption=caption,
            box=box_,
            show_lines=show_lines,
            show_edge=skow_edge,
            expand=expand,
            highlight=highlight,
        )

        index = [0]
        if restrict is None:
            def restrict(d) -> Literal[True]:  # pylint: disable=unused-argument
                return True
        row_styles: list[Style] = []
        for videos in self.videos_list:
            info_dict_list = [
                video_dict for video_dict in videos.list_all_videos if restrict(video_dict)]
            self._make_table(table, info_dict_list,
                             videos.colors, new_keys, index, row_styles)

        table.row_styles = row_styles
        my_console.print(table)

    def _make_table(self, table: Table,
                    info_dict_list: list[EntryInPlaylist | VideoInfoDict],
                    colors: "Videos._Colors",
                    keys: list[TableKey],
                    latest_idx: list[int],
                    row_styles: list[Style]) -> None:
        """색을 입혀서 열을 지정. 캡션은 밖에서 처리. idx는 밖에서 받아오기"""
        # 색은 직접 글씨에 입힘. 배경에도 색 입혀야 함 << 끊기거나 덮일까봐, 그냥 밖에서 리스트 두고 스타일을 하나씩 넣은 뒤 나중에 row_styles에 반영
        for video_dict in info_dict_list:  # 각 비디오 딕셔너리마다
            row_style = next(colors)
            row: list[Any] = latest_idx[:]
            for k in keys:
                row.append(k.formatter(video_dict.get(
                    k.key), **k.formatter_kwargs))
            table.add_row(*map(str, row))
            latest_idx[0] += 1
            # 배경에 색 입히기
            if video_dict.get("availability") != "public":
                row_style += Style(bgcolor="red", strike=True)
            elif video_dict.get("is_repeated"):
                row_style += Style(bgcolor="yellow")
            elif video_dict.get("is_downloaded"):
                row_style += Style(bgcolor="green")
            row_styles.append(row_style)

    def calculate_table_info(self) -> dict:
        """자신 비디오스의 종류별 영상 갯수 등을 세서 정보를 딕셔너리로 반환하는 함수"""
        return {}

    def format_table_info(self, table_info: dict = None) -> str:
        """딕셔너리로 받은 정보에 rich 형식으로 색 입혀서 내보내는 함수. 이 함수의 기능이 필요할 시 table_info에 값을 전달하여 사용"""
        if table_info is None:
            table_info = self.calculate_table_info()

        return "test"


class Videos(VideoListsManageMixin, DictListTransformMixin, VideosTableMixin):
    """메인에서 업데이트 호출 > 
    메인 내에서 컬러랑 da 먼저 직접 호출 > 
    비디오스 분류에서 자체 정의 업데이트로 업데이트하고 super 호출 > 
    사칙연산에서 업데이트하고 super 호출 안함.
    """
    class _Colors:
        """햇갈리니까 이름을 color로 바꿈. (원랜 style인데). 반복되는 색은 next(객체명)으로 호출"""

        def __init__(self, styles: list[Style | str] | tuple[Style | str, ...] = ("none", "dim")):
            self._idx: int = 0
            self.color_list: list[Style] = [s if isinstance(
                s, Style) else Style.parse(s) for s in styles]
            self.color: Style = self.color_list[0]

        def update(self):
            """이번에는 스타일스가 한칸짜리면 그냥 냅두기(dim은 열 표기에 사용됨)"""
            self.color_list = [s if isinstance(
                s, Style) else Style.parse(s) for s in self.color_list]
            self.color = self.color_list[0]

        def __iter__(self) -> Self:
            return self

        def __next__(self) -> Style:
            if self._idx >= len(self.color_list):
                self._idx = 0
            result = self.color_list[self._idx]
            self._idx += 1
            return result

    class DownArchive:
        def __init__(self, dir_: str = "", name: str = "") -> None:
            self.down_archive_dir = dir_
            self.down_archive_name = name

        def inherit_other_da(self):
            pass

        def bring_id_list(self) -> list[str]:
            """파일 읽어오기,, 딕셔너리에 is_da넣기"""
            down_archive = read_str_from_file(
                f"{self.down_archive_dir}\\{self.down_archive_name}")
            if down_archive:  # if 안붙이면 마지막줄에 공백에서 오류
                return [line.split()[1] for line in down_archive.split("\n") if line]
            else:
                return []

        def check_is_downloaded(self, id_to_check: str):
            pass

        def del_(self, id_: str):  # 이건 만드려면 da 재작성도 정의 필요
            pass
        # 무결성은 과하다 싶은데, 할일도 많고 멍청하게 다 지워버리지 않는 한 의미도 적음

    def __init__(
        self,
        playlist_url: str,
        video_bring_restrict: Callable[[EntryInPlaylist], bool] = None,
        playlist_title: str = "",
        inner_folder_split: Literal["%(upload_date>%Y.%m)s",
                                    "%(uploader)s", "%(playlist)s"] | str = "",
        styles: list[Style | str] | Style | str | None = None,
        split_chapter: bool = False,
        update_playlist_data: bool = True,
        # custom_da: bool = False,
        artist_name: str = "",
        album_title: str = "",
    ):
        """
        비디오스 객체의 da_name이 'custom'이거나 none이면 커스텀 경로로 지정됨
        Args:
            playlist_url: 메니져에서 읽어오고 구체화 시에 사용됨
            video_bring_restrict: 가져올 개별 영상 목록을 지정하는 함수. 기본적으로는 전부 가져옴.
            playlist_title: 하나의 플레이리스트를 저장할 폴더명. 플레이리스트명으로 자동지정됨.
            inner_folder_split: 내부에 폴더로 나눔. '%(upload_date>%Y.%m)s' (날짜 월별로 묶기), '%(uploader)s' (업로더 채널명으로 묶기), '%(playlist)s' (플레이리스트 이름으로 묶기). 자세한 건 https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#output-template 의 출력 탬플릿 참조.
            styles: 첫번째 스타일은 표나 정보 등에 사용됨. 스타일 리스트나 스타일, 문자열로 지정가능. 기본적으로는 채널 썸내일에서 주요 색 가져옴. 자세한 건 https://rich.readthedocs.io/en/stable/style.html 참조
            split_chapter: 챕터별로 영상을 분리할지 여부.
            update_playlist_data: 플리 데이터를 수정할지 여부
            custom_da: 다운로드 아카이브를 커스텀 경로에 저장할지 여부
            artist_name: 작곡가로 들어갈 이름. 기본적으로 채널명으로 자동지정됨.
            album_title: 엘범 제목. 기본적으로 플리명으로 자동지정됨.

        """
        # 메니져가 정의해주는 변수
        self.playlist_info_dict: ChannelInfoDict | PlaylistInfoDict = {}
        self.down_archive = self.DownArchive()
        self.channel_name = ""
        self.video_path = ""
        self.thumbnail_path = ""
        self.error_path = ""
        self.temp_path = ""

        def check_is_repeated(video_dict: VideoInfoDict) -> bool:
            # 기존은 list_not_repeated 정의하고 for문 돌면서 넣은 뒤 이 리스트에 있으면 중복에 넣고 이 리스트로 다운 가능/불가능 정했었음.
            if video_dict.get("id") in bring_key_list(self.list_repeated, "id"):  # type: ignore
                return True  # 중복이면
            else:  # 중복 아니면
                return False

        self.additional_keys: dict[str, Callable[[VideoInfoDict], Any]] = {
            "repeated": check_is_repeated,  # 중복 분류는 구현이 어려움. 중복 확인만 하기
            "is_downloaded": lambda video_dict: (
                True if video_dict.get(
                    "id") in self.down_archive.bring_da_list() else False
            ),
        }

        self.pl_folder_name = playlist_title
        self.playlist_url = playlist_url
        self.video_bring_restrict: Callable[[
            EntryInPlaylist], bool] = video_bring_restrict if video_bring_restrict else lambda dict_: True

        self.update_playlist_data = update_playlist_data
        self.inner_split_by = inner_folder_split
        self.split_chapter = split_chapter
        self.artist = artist_name
        self.album = album_title

        self.list_all_videos: list[VideoInfoDict | EntryInPlaylist] = []
        self.list_can_download: list[VideoInfoDict | EntryInPlaylist] = []
        # 비공개, 맴버십 온리, 최초공개 등.
        self.list_cannot_download: list[VideoInfoDict | EntryInPlaylist] = []
        self.list_repeated: list[VideoInfoDict | EntryInPlaylist] = []  # 중복 id

        self.sort_by: tuple[str, bool] = (
            "upload_date", False)  # 기본으로 업로드 날짜, 내림차순 정렬

        if isinstance(styles, list) or styles is None:
            self.styles: list[str | Style] | None = styles  # none이나 리스트면 그대로
        else:  # 아니면 (1개짜리면) 리스트로 바꿈
            if isinstance(styles, Style):
                self.styles = [styles, Style(dim=True) + styles]
            else:  # 문자열이면
                self.styles = [styles, Style(dim=True) + Style.parse(styles)]

        # self.style: Style | str = self.styles[0] if self.styles else "none"
        self.colors = self._Colors()

    def change_value(
        self,
        playlist_title: str = "",
        inner_folder_split: (
            Literal["%(upload_date>%Y.%m)s",
                    "%(uploader)s", "%(playlist)s"] | str
        ) = "",
        styles: list[Style | str] | Style | str | None = None,
        split_chapter: bool = False,
        custom_da: bool = False,
        artist_name: str = "",
        album_title: str = "",
    ) -> "Videos":
        if playlist_title:
            self.pl_folder_name = playlist_title
        if inner_folder_split:
            self.inner_split_by = inner_folder_split
        if styles:
            self.styles = styles  # type:ignore
        if split_chapter:
            self.split_chapter = split_chapter
        if custom_da:
            self.custom_da = custom_da
        if artist_name:
            self.artist = artist_name
        if album_title:
            self.album = album_title
        return self

    def update(self) -> "Videos":
        """영상 순서 정렬, 스타일 객체 일괄화, 다운로드 리스트 키를 딕셔너리에 추가, 다운로드 경로가 커스텀이면 커스텀 경로로 수정, 중복시 중복 리스트로 이동, 다운로드 가능/불가능 구별
        availability에는 "private", "premium_only", "subscriber_only", "needs_auth", "unlisted" or "public" 존재 가능.
        이 중 다운로드 가능은 public뿐
        """
        # da 커스텀 체크는 da가져오기에서 처리
        # 스타일이 문자열이면 스타일 객체로
        self.styles = [
            Style.parse(style) if isinstance(style, str) else style
            for style in self.styles
        ]
        if len(self.styles) == 1:
            self.styles = [self.styles[0], self.styles[0] + Style(dim=True)]
        self.style = self.styles[0]

        self.sort(self.sort_by[0], self.sort_by[1])  # 이건 전체만 sort하면 됨

        list_not_repeated = []
        for video in self.list_all_videos:
            if video.get("id") not in list_not_repeated:  # 이 키가 처음이면
                list_not_repeated.append(video)
            else:  # 이 키가 중복이면
                self.list_repeated.append(video)

            for key, func in self.additional_keys.items():
                video[key] = func(
                    video
                )  # 기본적으로 중복 여부 체크와 다운여부 체크를 함. 여기서 중복일 시 repeated를 true로 설정

        self.list_can_download = [
            video
            for video in self.list_all_videos
            if video.get("availability") == "public" and not video.get("repeated")
        ]
        self.list_cannot_download = [
            video
            for video in self.list_all_videos
            if video.get("availability") != "public" and not video.get("repeated")
        ]
        # self.list_repeated = [video for video in self.list_all_videos if video.get('repeated')]  # 위에서 넣음
        return self

    def info(self, print_: bool = True) -> Panel:
        self.update()
        styles_str = ""
        for idx, style in enumerate(self.styles):
            styles_str += f"[{style}]{style}[/]"
            if idx != len(self.styles) - 1:
                styles_str += ", "

        path_info = self.video_path + (
            "" if not self.inner_split_by else f"/{self.inner_split_by}\n"
        )
        can_dl_len, cannot_dl_len, can_dl_filesize_sum = self.calculate_table_info()

        info: Panel = Panel(
            f"[{self.style}]채널명[/]: {self.channel_name}\n"
            f"[{self.style}]폴더명(플리명)[/]: {self.pl_folder_name}\n"
            # f"[{self.style}]url[/]: {self.playlist_url}\n"
            f"[{self.style}]영상 저장 경로[/]: {path_styler(path_info)}\n"
            # f"[{self.style}]임시 저장 경로[/]: {path_styler(self.temp_path)}\n"
            # f"[{self.style}]썸내일 저장 경로[/]: {path_styler(self.thumbnail_path)}\n"
            # f"[{self.style}]오류 경로[/]: {path_styler(self.error_path)}\n"
            f"[{self.style}]다운아카이브 경로[/]: {path_styler(self.down_archive_path)}\n"
            f"[{self.style}]다운아카이브 이름[/]: {self.down_archive_name}\n"
            f"[{self.style}]스타일[/]: {styles_str}\n"
            f"[{self.style}]다운로드 가능 영상 수[/]: {can_dl_len}, "
            f"[{self.style}]다운로드 불가능 영상 수[/]: {cannot_dl_len}, "
            f"[{self.style}]총 용량[/]: {format_byte_str(can_dl_filesize_sum)}\n"
            f"[{self.style}]아티스트명[/]: {self.artist} / [{self.style}]엘범명[/]: {self.album}",
            border_style=self.style,
        )
        if print_:
            my_console.print(info, highlight=False)
        return info

    def bring_list_from_key(
        self, key: MAJOR_KEYS
    ) -> list[int | str | float | list | dict]:
        """해당하는 키값의 리스트 반환"""
        return bring_key_list(self.list_can_download, key)

    def override_list(self, videos: "Videos") -> "Videos":
        """다른 속성은 유지하고 리스트만 덮어씌움"""
        self.list_all_videos = videos.list_all_videos
        return self

    def sort(self, order: MAJOR_KEYS, reverse: bool = False) -> "Videos":
        """
        키값으로 정렬
        Args:
            order: 정렬할 기준 키값(upload_date, filesize_approx...),
            reverse: 오름차순 여부
        """
        self.sort_by = order, reverse
        list_cannot_sort = [
            video for video in self.list_all_videos if video.get(order) is None
        ]  # none이면 빠지겠지
        list_can_sort = [
            video for video in self.list_all_videos if video.get(order) is not None
        ]
        # 정렬할 키값이 없는거는 다른 리스트에 빼놓고 분류 후 합친다
        list_can_sort.sort(
            key=lambda dict_: dict_.get(order), reverse=reverse
        )  # 분류 불가만 했으므로 기본값 필요 x
        self.list_all_videos = list_can_sort + list_cannot_sort
        # self.update()  # 이건 아마 다른 함수에서 쓸때 처리해서 상관 없을 듯
        return self

    def cut(
        self, start: int = None, end: int = None, pop_from_original: bool = True
    ) -> "Videos":
        """
        파이썬의 슬라이싱과 같은 구조
        Args:
            start: 시작 위치
            end: 끝 위치
            percent: 전체에 대한 퍼센트로 따질지 여부. 기본이라면 갯수로 따짐
            pop_from_original: true면 원본을 필터링함, false면 필터링한 걸 반환
            new_pl_folder_name: 폴더명을 바꿀거면 설정

        """
        new_videos: Videos = deepcopy(self)

        new_videos.list_all_videos = new_videos.list_all_videos[start:end]
        if pop_from_original:
            self.override_list(
                self - new_videos
            )  # 원본에서 뺌. 이게 false면 원본은 그대로임

        new_videos.update()

        return new_videos

    def filtering(
        self, opt: Callable[[InfoDict], bool], pop_from_original: bool = True
    ) -> "Videos":
        """
        조건에 맞는 것만 남겨서 반환하거나 원본을 변경
        Args:
            opt: lambda info_dict: '엘든링' in info_dict['name'] or '엘든 링' in info_dict['name']
            pop_from_original: true면 원본을 변경, false면 변경 안함. 둘 다 수정된거 반환함.
            new_pl_folder_name: 하위 폴더 이름 지정
        """
        new_videos: Videos = deepcopy(self)

        new_videos.list_all_videos = [
            new_videos.list_all_videos[idx]
            for idx, video_dict in enumerate(new_videos.list_all_videos)
            if opt(video_dict)
        ]
        if pop_from_original:
            self.override_list(
                self - new_videos
            )  # 원본에서 뺌. 이게 false면 원본은 그대로임

        new_videos.update()

        return new_videos

    def filtering_keyward(
        self,
        *keywards: str,
        find_in_descriptions: bool = False,
        find_in_comments: bool = False,
        pop_from_original: bool = True,
    ) -> "Videos":
        """제목, 설명, (댓글)에서 찾기"""
        new_videos_to_filter: Videos = deepcopy(self)
        new_videos_to_return: Videos = deepcopy(self)
        new_videos_to_return.list_all_videos = []

        for keyward in keywards:
            new_videos_to_return.list_all_videos += new_videos_to_filter.filtering(
                lambda dict_, keyward=keyward: keyward in dict_["title"]
            ).list_all_videos
            new_videos_to_return.list_all_videos += new_videos_to_filter.filtering(
                lambda dict_, keyward=keyward: keyward in dict_["description"]
                and find_in_descriptions
            ).list_all_videos

            def find_in_c(info_dict: dict, keyward=keyward) -> bool:
                if not find_in_comments or not info_dict.get("comments"):
                    return False
                else:
                    comment_text = "".join(
                        [(c.get("text")) for c in info_dict.get("comments")]
                    )
                    return keyward in comment_text

            new_videos_to_return.list_all_videos += new_videos_to_filter.filtering(
                find_in_c
            ).list_all_videos

        if pop_from_original:
            self.override_list(self - new_videos_to_return)
            # 원본에서 뺌. 이게 false면 원본은 그대로임

        return new_videos_to_return

    def show_table(
        self,
        keys_to_show: list[
            MAJOR_KEYS | tuple[MAJOR_KEYS,
                               Callable[[str | int | float | Any], str]]
        ] = None,
        show_lines: bool = False,
        show_edges: bool = True,
        print_: bool = True,
        restrict: Callable[[InfoDict], bool] = None,
    ) -> Table:
        """
        keys_to_show는 키 이름 또는 (키 이름,값에 적용할 함수명) 리스트임. 키가 없을 경우 Unknown반환.
        기본 keys_to_show:
        keys_to_show = [
            'title',
            ('upload_date', format_date),
            ('view_count', format_number),
            ('like_count', format_number),
            ('duration', format_time),
            ('filesize_approx', format_byte_str)]
        restrict: 예를 들어 lambda dict_: dict.get('availability') == 'public'
        다운아카 여부는 'is_downloaded'로 접근 가능
        Return:
            table
        """
        self.update()
        title = self.pl_folder_name
        can_dl_len, cannot_dl_len, can_dl_filesize_sum = self.calculate_table_info()
        caption = (
            f"[{self.style}]다운로드 가능 영상 수[/]: {can_dl_len}, "
            f"[{self.style}]다운로드 불가능 영상 수[/]: {cannot_dl_len}, "
            f"[{self.style}]총 용량[/]: {format_byte_str(can_dl_filesize_sum)}"
        )

        table = make_info_table(
            video_list=self.list_all_videos,
            keys_to_show=keys_to_show,
            title=title if print_ else None,
            caption=caption if print_ else None,
            style=self.style,
            row_style=self.styles[:3],
            print_=print_,
            print_title_and_caption=True,
            show_lines=show_lines,
            show_edges=show_edges,
            restrict=restrict,
            sort_by=self.sort_by,
        )
        # print_ 안하면 제목도 안나옴
        return table

    # def calculate_table_info(self) -> tuple[int, int, int]:
        # """
        # Return:
        # can_dl_len, cannot_dl_len, can_dl_filesize_sum(not formated)
        # """
        # can_dl_len = len(self.list_can_download)
        # cannot_dl_len = len(self.list_cannot_download)
        # can_dl_filesize_sum = sum(
        # [
        # video_dict.get("filesize_approx", 0)
        # for video_dict in self.list_can_download
        # if isinstance(video_dict.get("filesize_approx", 0), int)
        # ]
        # )
#
        # return can_dl_len, cannot_dl_len, can_dl_filesize_sum

    # 연산(합,차,교집합)함수: 집합으로 연산한 후 순서 재정렬해야 함. 필터가 클래스를 반환하는지 리스트를 반환하는지에 따라 이거에 클래스를 넣을지 리스트를 넣을지 달라짐.
    def __add__(self, other: "Videos") -> "Videos":
        # 이건 따로 역방향 연산을 정의하지 않으면 a+b는 a에서, b+a는 b에서 처리됨
        # __iadd__는 +=연산으로, 이거 하면 새 객체 반환임.
        new_videos = deepcopy(self)
        new_videos.list_all_videos = DictSetOperator.union(
            new_videos.list_all_videos, other.list_all_videos
        )
        new_videos.update()
        return new_videos

    def __sub__(self, other: "Videos") -> "Videos":
        new_videos = deepcopy(self)
        new_videos.list_all_videos = DictSetOperator.diff(
            new_videos.list_all_videos, other.list_all_videos
        )
        new_videos.update()
        return new_videos

    def __and__(self, other: "Videos") -> "Videos":
        """교집합: &메소드 사용"""
        new_videos = deepcopy(self)
        new_videos.list_all_videos = DictSetOperator.inter(
            new_videos.list_all_videos, other.list_all_videos
        )
        new_videos.update()
        return new_videos

import os
import traceback
from typing import Callable, Any, Literal
import yt_dlp  # type: ignore

from ..newtypes.formatstr import format_filename
from ..newtypes.ydl_types import VideoInfoDict, PlaylistInfoDict, ChannelInfoDict, EntryInPlaylist

from .timestamp_parser import parse_chapters


class ExtractChapter(yt_dlp.postprocessor.PostProcessor):
    """
    "pre_process" (after video extraction)
    "after_filter" (after video passes filter)
    "video" (after --format; before --print/--output)
    "before_dl" (before each video download)
    "post_process" (after each video download; default)
    "after_move" (after moving the video file to its final location)
    "after_video" (after downloading and processing all formats of a video)
    "playlist" (at end of playlist)
    """

    # ℹ️ See help(yt_dlp.postprocessor.PostProcessor)
    def run(self, information: VideoInfoDict):
        chapters = information.get("chapters")
        if chapters:
            self.to_screen(
                f"Already have chapters:{[chapter.get('title') for chapter in chapters]}"
            )
            return [], information

        video_duration = information.get("duration", None)

        # 설명란에서 추가
        description = information.get("description")
        if description:
            chapters = parse_chapters(description, video_duration)
            # 밑에 챕터 나오면 그걸로 덮어씌워짐. 기본 설명은 url인데 디스크립션으로 바꾸고(메타 디스크립션은 설명 그대로 삽입) 챕터를 다른 부분에서 찾으면 그걸로 변경
            information["meta_comment"] = description
            if chapters:
                information["chapters"] = chapters
                self.to_screen(
                    f"Embedded chapters from description:{[chapter.get('title') for chapter in chapters]}")
                return [], information

        # 댓글에서 추가
        comments = information.get("comments")
        if not comments:
            self.to_screen("Comment doesn't exists")
            return [], information

        for comment in comments:
            chapters = parse_chapters(comment.get("text", ""), video_duration)
            if chapters:
                information["chapters"] = chapters
                information["meta_comment"] = comment.get("text", "")
                self.to_screen(
                    f"Embedded chapters from comment:{[chapter.get('title') for chapter in chapters]}"
                )
                return [], information

        self.to_screen("No chapters to embed found!")
        return [], information


class ChangeInfoDict(yt_dlp.postprocessor.PostProcessor):
    def __init__(self, downloader=None, info_dict: VideoInfoDict = None) -> None:
        super().__init__(downloader=downloader)
        self.info_dict: VideoInfoDict = info_dict if info_dict else {}

    @staticmethod
    def simplify_long_types(long_types: list | tuple | dict | set) -> str:
        if isinstance(long_types, dict):
            long_types = list(long_types.keys())

        return ", ".join(long_types)[:40]

    def run(self, information):
        for key, value in self.info_dict.items():
            if value:
                value_to_change = self.simplify_long_types(value)

                if key in information:  # 기존값 변경시
                    existing_value = self.simplify_long_types(information[key])

                    self.to_screen(
                        f"Changed {key}: {existing_value} >> {value_to_change}"
                    )
                else:  # 신규 생성시
                    self.to_screen(f"Added {key}: {value_to_change}")

                information[key] = value

        return [], information


class Download:
    """값에 안전딕셔너리 씌우는건 밖에서 infod 접근해서 하기"""

    def __init__(self,
                 save_path: str,
                 urls: list[str] | str,
                 *,
                 filename_template: str = "{inner_folder}%(title)s (%(uploader)s).%(ext)s",
                 chaptername_template: str = "{inner_folder}%(title)s - %(section_title)s (%(uploader)s).%(ext)s",
                 inner_folder: str = "",
                 thumbnail_path: str = "",
                 download_archive_path: str = os.getcwd(),
                 download_archive_name: str = None,
                 temp_path: str = "",
                 split_chapters: Literal["separately",
                                         "in_video_named_folder", False] = False,
                 embed_info_json: bool = False,
                 progress_hook: Callable[[VideoInfoDict], None] = None,
                 concurrent_fragments: int = min(
                     32, (os.cpu_count() or 1) + 4),
                 ignore_errors: bool | Literal['only_download'] = "only_download",
                 skip_hls_or_dash: list[Literal["dash", "m3u8"]] | None = None,
                 logger=None,
                 quiet: bool = True,
                 progress_delta: float = 0,
                 additional_info_dict: VideoInfoDict = None) -> None:
        """

        Args:
            save_path: 파일을 저장할 경로
            urls: 영상의 url 또는 url 리스트
            filename_template: 
            chaptername_template: 
            inner_folder: 
            thumbnail_path: 
            download_archive_path: 
            download_archive_name: 
            temp_path: 
            split_chapters: 
            embed_info_json: 
            progress_hook: 
            concurrent_fragments: 
            ignore_errors: 
            skip_hls_or_dash: 
            logger=None,
            quiet: 
            progress_delta: 
            additional_info_dict: 
        """
        if isinstance(urls, str):
            urls = [urls]
        if inner_folder:
            inner_folder += "\\"

        self.urls = urls
        self.additional_info_dict = additional_info_dict

        self.ydl_opts: dict[str, Any] = {
            "concurrent_fragment_downloads": concurrent_fragments,
            "extractor_args": {"youtube": {"skip": ["translated_subs"]}},
            "noprogress": False,
            "outtmpl": {
                "default": inner_folder + filename_template,
                "chapter": inner_folder + chaptername_template,
            },
            "paths": {
                "home": save_path,
                "chapter": save_path,  # 챕터는 폴더에 넣을까?
                "temp": temp_path if temp_path else f"{save_path}\\temp",
                "thumbnail": (thumbnail_path if thumbnail_path else f"{save_path}\\thumbnails"),
            },
            "postprocessors": [
                {
                    "format": "jpg",
                    "key": "FFmpegThumbnailsConvertor",
                    "when": "before_dl"
                },
                {
                    "already_have_subtitle": False,
                    "key": "FFmpegEmbedSubtitle"
                },
                {
                    "already_have_thumbnail": True,
                    "key": "EmbedThumbnail"
                },
                {
                    "add_chapters": True,
                    "add_infojson": embed_info_json,
                    "add_metadata": True,
                    "key": "FFmpegMetadata",
                }
            ],
            "subtitleslangs": ["kr", "jp", "en"],
            "writesubtitles": True,
            "quiet": quiet,
            "writethumbnail": True,  # 없으면 썸내일 안들어감
            "ignoreerrors": ignore_errors,
            "nopart": True,
            "progress_delta": progress_delta,
        }

        if split_chapters:
            self.ydl_opts["postprocessors"].append({
                "force_keyframes": False,
                "key": "FFmpegSplitChapters"
            })
        if progress_hook:
            self.ydl_opts["progress_hooks"] = [progress_hook]
        if download_archive_name:  # 이름 빈칸으로 하면 x
            self.ydl_opts["download_archive"] = (
                f"{download_archive_path}\\{download_archive_name}"
                if download_archive_path else download_archive_name)
        if skip_hls_or_dash:
            self.ydl_opts["extractor_args"]["youtube"]["skip"] += skip_hls_or_dash
        if logger:
            self.ydl_opts["logger"] = logger
        # ydl은 어처피 ydl_opt가 밑에서 더 추가돼야 하므로 그냥 with로 쓰기

    def download_video(self,
                       restrict_format: str = "[height<=1080]",
                       ext: str = "mkv") -> int:

        ydl_opts = self.ydl_opts
        ydl_opts["format"] = f"bestvideo{restrict_format}+bestaudio/best{restrict_format}"
        ydl_opts["merge_output_format"] = ext

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.add_post_processor(ChangeInfoDict(
                info_dict=self.additional_info_dict), when='before_dl')
            error_code = ydl.download(self.urls)

        return error_code

    def download_music(self):
        """"final_ext": "mka",
        "format": "bestaudio/best",
        {
                "key": "FFmpegExtractAudio",
                "nopostoverwrites": False,
                "preferredcodec": "best",
                "preferredquality": "0",
            },
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mka"
            },"""
        pass


def download_video(
    *,
    video_path: str,
    urls: list[str] | str,
    inner_folder: str = "",
    thumbnail_path: str = "",
    download_archive_path: str = os.getcwd(),
    download_archive_name: str = "",
    temp_path: str = "",
    split_chapters: bool = False,
    embed_info_json: bool = False,
    restrict_format: str = "[height<=1080]",
    ext: str = "mkv",
    progress_hook: Callable[[dict], None] = None,
    concurrent_fragments: int = 3,
    ignore_errors: bool | str = "only_download",
    skip_hls_or_dash: list[str] | None = None,
    logger=None,
    quiet: bool = True,
    progress_delta: float = 0,
    change_info_dict: VideoInfoDict = None,
) -> int:
    """
    skip_hls_or_dash: None(https), 'hls'(hls 스킵), 'dash'(dash 스킵)
    로거는 객체로 전달해야 함

    yt-dlp --quiet --concurrent-fragments 3 --quiet --format "bestvideo[height<=720]+bestaudio/best[height<=720]"
    --output "[%(upload_date>%y.%m.%d)s] %(title)s (%(uploader)s).%(ext)s"
    --paths "thumbnail:dirname" --paths "home:dirname"
    --write-thumbnail --convert-thumbnails jpg --embed-thumbnail
    --embed-chapters --embed-info-json --embed-metadata --embed-subs
    --merge-output-format mkv
    --write-comments --extractor-args "youtube:comment_sort=top;max_comments=10,10,0,0;lang=ko;skip=translated_subs"
    --download-archive "video_download_archive.txt"
    https://www.youtube.com/watch?v=e69muZQyTXY
    """
    # "private", "premium_only", "subscriber_only", "needs_auth", "unlisted" or "public"
    if isinstance(urls, str):
        urls = [urls]
    if inner_folder:
        inner_folder += "\\"

    ydl_opts: dict[str, Any] = {
        "concurrent_fragment_downloads": concurrent_fragments,
        "extractor_args": {"youtube": {"skip": ["translated_subs"]}},
        "format": f"bestvideo{restrict_format}+bestaudio/best{restrict_format}",
        "merge_output_format": ext,
        "noprogress": False,
        "outtmpl": {
            "default":
            f"{inner_folder}%(title)s (%(uploader)s) [%(upload_date>%y.%m.%d)s].%(ext)s",
            "chapter":
            f"{inner_folder}%(title)s - %(section_title)s (%(uploader)s) "
            f"[%(upload_date>%y.%m.%d)s].%(ext)s",
        },
        "paths": {
            "home": video_path,
            "chapter": video_path,
            "temp": f"{video_path}\\temp" if not temp_path else temp_path,
            "thumbnail": (thumbnail_path if thumbnail_path else f"{video_path}\\thumbnails"),
        },
        "postprocessors": [
            {
                "format": "jpg",
                "key": "FFmpegThumbnailsConvertor",
                "when": "before_dl"
            },
            {
                "already_have_subtitle": False,
                "key": "FFmpegEmbedSubtitle"
            },
            {
                "already_have_thumbnail": True,
                "key": "EmbedThumbnail"
            },
            {
                "add_chapters": True,
                "add_infojson": embed_info_json,
                "add_metadata": True,
                "key": "FFmpegMetadata",
            }
        ],
        "subtitleslangs": ["kr", "jp", "en"],
        "writesubtitles": True,
        "quiet": quiet,
        "writethumbnail": True,  # 없으면 썸내일 안들어감
        "ignoreerrors": ignore_errors,
        "nopart": True,
        "progress_delta": progress_delta,
    }
    if split_chapters:
        ydl_opts["postprocessors"].append({
            "force_keyframes": False,
            "key": "FFmpegSplitChapters"
        })
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]
    if download_archive_name:  # 이름 빈칸으로 하면 x
        ydl_opts["download_archive"] = (
            f"{download_archive_path}\\{download_archive_name}"
            if download_archive_path else download_archive_name)
    if skip_hls_or_dash:
        ydl_opts["extractor_args"]["youtube"]["skip"] += skip_hls_or_dash
    if logger:
        ydl_opts["logger"] = logger

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(ChangeInfoDict(info_dict=change_info_dict),
                               when="before_dl")
        error_code = ydl.download(urls)

    return error_code


def download_music(
    *,
    music_path: str,
    urls: list[str] | str,
    inner_folder: str = "",
    thumbnail_path: str = "",
    download_archive_path: str = "",
    download_archive_name: str = "",
    temp_path: str = "",
    split_chapters: bool = False,
    embed_info_json: bool = False,
    #    album: str = "%(uploader)s",  # playlist필드는 없음. 엘범에는 inner넣기
    #    artist: str = "%(uploader)s",  # 트랙이 뭐 들어가는지 확인
    progress_hook: Callable[[dict], None] = None,
    concurrent_fragments: int = 3,
    skip_hls_or_dash: list[str] | None = None,
    #    chapter: list[dict[str, str | int]] = None,
    ignore_errors: bool | str = "only_download",
    logger=None,
    quiet: bool = True,
    progress_delta: float = 0,
    change_info_dict: VideoInfoDict = None,
) -> int:
    """
    skip_hls_or_dash: None(https), 'hls'(hls 스킵), 'dash'(dash 스킵)
    로거는 객체로 전달해야 함

    m4a, 자막, 오디오만, 챕터 분리 다운로드 가능, 제목 수정
    여긴 썸내일 제거하면 미리보기가 아니라 꼬깔콘이 나옴
    엘범 부분에는 플리명 넣으면 알아서 됨
    python cli_to_api.py yt-dlp --quiet --no-progress --format "bestaudio/best" --concurrent-fragments 3
    --extract-audio --audio-quality 0 --remux-video mka
    --output "home:%(title)s (%(uploader)s).%(ext)s"
    --output "chapter:%(section_title)s - %(title)s (%(uploader)s).%(ext)s"
    --output "thumbnail:[%(upload_date>%y.%m.%d)s] %(title)s (%(uploader)s).%(ext)s"
    --paths "home:dirname" --paths "chapter:dirname" --paths "thumbnail:dirname"
    --convert-thumbnails jpg --embed-thumbnail --write-thumbnail
    --embed-chapters --embed-info-json --embed-metadata
    --write-comments --extractor-args "youtube:comment_sort=top;max_comments=10,10,0,0;lang=ko;skip=translated_subs"
    --split-chapters --download-archive "music_download_archive.txt"
    --parse-metadata "" --parse-metadata "" --parse-metadata ""
    https://youtu.be/jMSXPPSmsVo?si=C-x0Ah8OlTaLq2O6

    --parse-metadata "description:(?s)(?P<meta_comment>.+)"
    """
    if isinstance(urls, str):
        urls = [urls]
    if inner_folder:
        inner_folder += "\\"

    ydl_opts: dict[str, Any] = {
        "concurrent_fragment_downloads": concurrent_fragments,
        "extractor_args": {"youtube": {"skip": ["translated_subs"]}},
        "final_ext": "mka",
        "format": "bestaudio/best",
        "noprogress": False,
        "outtmpl": {
            "default": f"{inner_folder}%(title)s (%(uploader)s).%(ext)s",
            "chapter": f"{inner_folder}%(section_title)s - %(title)s (%(uploader)s).%(ext)s",
        },
        "paths": {
            "home": music_path,
            "chapter": music_path,
            "temp": f"{music_path}\\temp" if not temp_path else temp_path,
            "thumbnail": thumbnail_path if thumbnail_path else f"{music_path}\\thumbnails",
        },
        "postprocessors": [
            {
                "format": "jpg",
                "key": "FFmpegThumbnailsConvertor",
                "when": "before_dl"
            },
            {
                "key": "FFmpegExtractAudio",
                "nopostoverwrites": False,
                "preferredcodec": "best",
                "preferredquality": "0",
            },
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mka"
            },
            {
                "add_chapters": True,
                "add_infojson": embed_info_json,
                "add_metadata": True,
                "key": "FFmpegMetadata",
            },
            #    {'actions': [(yt_dlp.postprocessor.metadataparser.MetadataParserPP.interpretter,
            #  album,
            #  '%(meta_album)s'),
            # (yt_dlp.postprocessor.metadataparser.MetadataParserPP.interpretter,
            #  artist,
            #  '%(meta_artist)s')],
            # 'key': 'MetadataParser',
            # 'when': 'pre_process'},
            # {'already_have_subtitle': False,
            #  'key': 'FFmpegEmbedSubtitle'}
        ],
        # "subtitleslangs": ["kr", "jp", "en"],
        # 'writesubtitles': True,
        "quiet": quiet,
        "writethumbnail": True,
        "ignoreerrors": ignore_errors,
        "nopart": True,
        "progress_delta": progress_delta,
    }

    if split_chapters:
        ydl_opts["postprocessors"].append({
            "force_keyframes": False,
            "key": "FFmpegSplitChapters"
        })
    else:  # 챕터 나누지 않으면
        ydl_opts["postprocessors"].append({
            "already_have_thumbnail": True,
            "key": "EmbedThumbnail"
        })  # 이거 양립 안되나
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]
    if download_archive_name:  # 이름 빈칸으로 하면 x
        ydl_opts["download_archive"] = (
            f"{download_archive_path}\\{download_archive_name}"
            if download_archive_path else download_archive_name)
    if skip_hls_or_dash:
        ydl_opts["extractor_args"]["youtube"]["skip"] += skip_hls_or_dash
    if logger:
        ydl_opts["logger"] = logger

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(ChangeInfoDict(info_dict=change_info_dict),
                               when="before_dl")  # 메타데이터 임베딩 하기 전이어야 함
        error_code = ydl.download(urls)

    return error_code


def bring_playlist_info(url: str, logger=None, change_lang: bool = False) -> PlaylistInfoDict | ChannelInfoDict:
    """플리의 title수정
    로거는 객체로 전달해야 함

    비디오별 타이틀은 그대로임. 이건 아래에 엔트리에서 수정
    parse-metadata는 각 영상마다 작동하지만 결과는 전체에만 적용되는 듯
    yt-dlp --flat-playlist --quiet --skip-download
    --extractor-args "youtube:lang=ko;skip=translated_subs"
    """
    ydl_opts: dict[str, Any] = {
        "extract_flat": "in_playlist",
        "noprogress": True,
        "quiet": True,
        "skip_download": True,
        "extractor_args": {
            "youtube": {
                "skip": ["translated_subs"],
                # 이게 될지 모름. 되는지 보고 실 사용시에는 분리해서 두번 긁어오기.

            }},
    }
    if logger:
        ydl_opts["logger"] = logger
    if change_lang:
        ydl_opts["extractor_args"]["youtube"]["lang"] = ['ko']

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict: PlaylistInfoDict | ChannelInfoDict = ydl.extract_info(
            url, download=False)
        info_dict["old_title"] = info_dict.get("title", "")
        info_dict["title"] = format_filename(info_dict.get("title", ""))
        info_dict = ydl.sanitize_info(info_dict)

    return info_dict


def bring_video_info(url: str,
                     playlist_name: str = "", playlist_uploader: str = "",
                     logger=None) -> tuple[VideoInfoDict, str | None]:
    """
    전체 수, 댓글 전체수는 제한 없고 각 댓글마다 5개씩 20개 가져옴
    webpage_url이 아니라 url임.
    yt-dlp --skip-download --quiet
    --write-comments --extractor-args "youtube:comment_sort=top;max_comments=all,20,all,5;lang=ko;skip=translated_subs"
    https://youtu.be/FMn6hSMNXZQ?si=qipAvVcCy8RntzEK
    """
    ydl_opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "extractor_args": {
            "youtube": {
                "comment_sort": ["top"],
                "max_comments": ["all", "20", "all", "5"],
                "skip": ["translated_subs"],
            }
        },
        "getcomments": True,
        "noprogress": True,
        "quiet": True,
        "skip_download": True,
        "writeinfojson": True,
    }
    if logger:
        ydl_opts["logger"] = logger

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.add_post_processor(ExtractChapter(), when="after_filter")
            info_dict: VideoInfoDict = ydl.extract_info(url, download=False)
            info_dict["old_title"] = info_dict.get("title", "")
            info_dict["title"] = format_filename(info_dict.get("title"))
            if playlist_name:  # 비디오에서는 플리명을 모르기 때문에
                info_dict["playlist"] = playlist_name
            if playlist_uploader:
                info_dict["playlist_uploader"] = playlist_uploader

            # for key in ["formats", "requested_formats", "automatic_captions", "heatmap", "thumbnails", "heatmap",]:
                # if key in info_dict.keys():
                # del info_dict[key]

            info_dict = ydl.sanitize_info(info_dict)
            tb = None
        except yt_dlp.DownloadError:
            info_dict = {}
            tb = traceback.format_exc()

    return info_dict, tb


# def change_video_dict_list(playlist_info_dict: dict) -> list[dict]:  # 구버전 함수
    # """채널 받아서 이름 포메팅 된 entries 내의 동영상 딕셔너리 리스트 반환"""
    # entries = playlist_info_dict.get("entries")
    # video_list: list[dict] = []  # 비디오 딕셔너리 목록 담을 리스트
    # 만약 엔트리에 플리가 있으면 그거 붙이고 비디오면 append
    # for entry in entries:
    # if entry.get("_type") == "playlist":
    # video_list += entry.get("entries")  # +=과 같은거임
    # elif entry.get("_type") == "url":  # 비디오면
    # video_list.append(entry)
    # 비디오 타이틀 변경. 이건 플리에서 바꾸는건데 플리에선 각 비디오 이름은 안바뀌므로
    # for video in enumerate(video_list):
    # video["old_title"] = video.get("title")
    # video["title"] = format_filename(video.get("title"))
    # video["webpage_url"] = video.get("url")
#
    # return video_list


def extract_playlist_entries(data_playlist: PlaylistInfoDict) -> list[EntryInPlaylist]:
    """두개의 플리를 제공받아 이름을 변경하고 플레이리스트 필드를 체움. 채널의 경우는 이 함수를 여러번 적용"""
    entries = data_playlist["entries"]

    for idx, entry in enumerate(entries):
        # 구버전 이름부터 한글 이름으로. 플리를 두번 가져와서 이름만 수정한 플리로 제공
        entry["old_title"] = entry['title']
        entry["title"] = format_filename(entry["title"])
        entry['playlist'] = data_playlist["title"]
        entry["playlist_count"] = idx
    return entries

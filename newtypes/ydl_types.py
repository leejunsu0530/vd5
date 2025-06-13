from typing import Literal, TypedDict, TypeAlias, TypeGuard


MAJOR_KEYS = Literal[
    "id",
    "title",
    "uploader",
    "channel",
    "playlist",
    "upload_date",
    "duration",
    "view_count",
    "like_count",
    "live_status",
    "availability",
    "filesize_approx",
] | str


LiveStatus: TypeAlias = Literal["not_live", "is_live",
                                "is_upcoming", "was_live", "post_live"]
Availability: TypeAlias = Literal["private", "premium_only",
                                  "subscriber_only", "needs_auth", "unlisted", "public"]


class EntryInPlaylist(TypedDict, total=False):  # 플리 내 간단한 개별 영상 데이터.
    _type: str
    id: str
    url: str
    title: str
    description: str
    tags: list[str] | None
    duration: int
    channel_id: str
    channel: str
    channel_url: str
    uploader: str
    uploader_id: str | None
    uploader_url: str | None
    thumbnails: list["Thumbnail"]
    availability: Availability | None
    view_count: int
    live_status: LiveStatus | None
    old_title: str
    playlist: str
    playlist_count: int  # 일단 여기만 추가하고 밑에도 필요할진 모름


class PlaylistInfoDict(TypedDict, total=False):  # 타입힌트 할때 굳이 Playlist|Channel로 할 필요x
    id: str
    title: str
    description: str
    thumbnails: list["Thumbnail"]
    channel: str
    channel_id: str
    uploader_id: None  # 헨들러 형식 아님
    uploader: str
    channel_url: str
    uploader_url: None
    _type: str
    entries: list[EntryInPlaylist]
    webpage_url: str
    old_title: str


class ChannelInfoDict(TypedDict, total=False):
    id: str
    title: str
    description: str
    thumbnails: list["Thumbnail"]
    channel: str
    channel_id: str
    uploader_id: str  # 헨들러
    uploader: str
    channel_url: str
    uploader_url: str
    _type: str
    entries: list[PlaylistInfoDict]
    webpage_url: str
    old_title: str


class VideoInfoDict(TypedDict, total=False):
    id: str
    title: str
    description: str
    channel_id: str
    channel_url: str
    duration: int
    view_count: int
    webpage_url: str
    tags: list[str]
    live_status: LiveStatus
    chapters: list["Chapter"]
    like_count: int
    channel: str
    uploader: str
    uploader_id: str
    uploader_url: str
    upload_date: str
    availability: Availability
    duration_string: str
    is_live: bool
    was_live: bool
    comments: list["Comment"]
    ext: str
    protocol: str
    filesize_approx: int
    filesize: None | int
    old_title: str
    meta_album: str
    meta_artist: str
    meta_comment: str
    playlist: str
    playlist_uploader: str
    purl: str


class Comment(TypedDict, total=False):
    id: str
    parent: str
    text: str
    like_count: int
    author_id: str
    author: str
    author_thumbnail: str
    author_is_uploader: bool
    author_is_verified: bool
    author_url: str
    is_favorited: bool
    _time_text: str
    timestamp: int
    is_pinned: bool


class Thumbnail(TypedDict, total=False):
    url: str | Literal["avatar_uncropped", "banner_uncropped"]
    id: str
    preference: int
    height: int | None
    width: int | None
    resolution: str | None


class Chapter(TypedDict, total=False):
    title: str
    start_time: int | float
    end_time: int | float


def is_channel_info_dict(info_dict: ChannelInfoDict | PlaylistInfoDict | dict) -> TypeGuard[ChannelInfoDict]:
    entries = info_dict['entries']
    entry_type = entries[0]['_type']
    return entry_type == "playlist"  # 채널이면 엔트리 내에 플리 있음


def is_playlist_info_dict(info_dict: ChannelInfoDict | PlaylistInfoDict | dict) -> TypeGuard[PlaylistInfoDict]:
    entries = info_dict['entries']
    entry_type = entries[0]['_type']
    return not entry_type == "playlist"  # 플리이면 엔트리 내에 영상 있음

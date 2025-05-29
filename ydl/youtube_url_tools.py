# import re
from typing import Literal
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from bs4.element import Tag, NavigableString


def find_id(url: str) -> tuple[Literal["channel", "channel__tab", "playlist", "[Failed]"], str]:
    """
    URL에서 채널 핸들 또는 플레이리스트 ID를 추출합니다.
    Args:
        url: YouTube URL
    Returns:
        tuple: 
            첫 번째 값은 id의 종류를 나타내며, 채널, 채널의 탭, 플레이리스트, 오류 메시지 중 하나입니다.
            두 번째 값은 다음 중 하나입니다:
                - 채널 핸들: "@handle"
                - 채널 탭: "@handle__videos", "@handle__playlists" 등
                - 플레이리스트 ID: "PL~"로 시작
                - 실패 시: 실패 메시지
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url.lstrip('/')

    if url.rstrip('/').endswith('/featured'):
        url = url.rstrip('/').rsplit('/featured', 1)[0]

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path
    query_params = parse_qs(parsed.query)

    # 🎯 영상 URL은 무시
    if ('watch' in path and 'v=' in parsed.query) or 'youtu.be' in domain or '/shorts/' in path or '/embed/' in path:
        return "[Failed]", f"영상 URL은 처리하지 않습니다: {url}"

    # 🎯 플레이리스트 ID 추출
    if 'list' in query_params:
        return "playlist", query_params['list'][0]

    # 🎯 탭 경로 추출 (videos, playlists 등), featured는 제거
    segments = path.strip('/').split('/')
    tab_segment = ''
    for seg in segments:
        if seg.lower() == 'featured':
            continue
        if seg.lower() in {'videos', 'playlists', 'community', 'channels', 'about', 'streams', 'shorts'}:
            tab_segment = '__' + seg
            break

    # 🎯 @handle 포함된 경우 바로 추출
    if '/@' in path:
        for segment in path.split('/'):
            if segment.startswith('@'):
                if tab_segment:
                    return "channel__tab", segment + tab_segment
                else:
                    return "channel", segment

    # 🎯 리디렉션 또는 HTML 파싱
    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
    except requests.RequestException:
        return "[Failed]", f"채널 핸들 추출 실패: {url}"

    final_url = response.url
    parsed_final = urlparse(final_url)
    final_path = parsed_final.path

    # 홈화면이면 실패 처리
    if parsed_final.netloc.endswith('youtube.com') and final_path in ['', '/']:
        return "[Failed]", f"채널 핸들 추출 실패: {url}"

    # 리디렉션 결과에서 핸들 추출
    if '/@' in final_path:
        for segment in final_path.split('/'):
            if segment.startswith('@'):
                if tab_segment:
                    return "channel__tab", segment + tab_segment
                else:
                    return "channel", segment

    # HTML 파싱에서 핸들 추출
    soup = BeautifulSoup(response.text, 'html.parser')
    handle = None

    # canonical
    canonical_link = soup.find('link', rel='canonical')
    if isinstance(canonical_link, Tag):
        raw_href = canonical_link.get('href', '')
        href = str(raw_href) if isinstance(raw_href, NavigableString) else ""
        if '/@' in href:
            href_path = urlparse(href).path
            for segment in href_path.split('/'):
                if segment.startswith('@'):
                    handle = segment
                    break

    # og:url
    if not handle:
        og_tag = soup.find('meta', property='og:url')
        if isinstance(og_tag, Tag):
            raw_href = og_tag.get('content', '')
            href = str(raw_href) if isinstance(
                raw_href, NavigableString) else ""
            if '/@' in href:
                href_path = urlparse(href).path
                for segment in href_path.split('/'):
                    if segment.startswith('@'):
                        handle = segment
                        break

    if handle:
        if tab_segment:
            return "channel__tab", handle + tab_segment
        else:
            return "channel", handle
    else:
        return "[Failed]", f"채널 핸들 추출 실패: {url}"


if __name__ == '__main__':
    from time import time
    from rich import print as rprint
    test_urls = [
        "https://www.youtube.com/@GoogleDevelopers",
        "https://www.youtube.com/@GoogleDevelopers/videos",
        "https://www.youtube.com/@GoogleDevelopers/featured",
        "https://www.youtube.com/@GoogleDevelopers/featured/",
        "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw",
        "https://www.youtube.com/c/YouTubeCreators/featured",
        "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw/videos",
        "https://www.youtube.com/playlist?list=PL590L5WQmH8fJ54F13T4AJ57c5m4FBHO2",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL590L5WQmH8fJ54F13T4AJ57c5m4FBHO2",
        "https://www.youtube.com/@geekble_kr/streams",
        "https://www.youtube.com/@geekble_kr/shorts"
    ]

    for url_ in test_urls:
        start_time = time()
        rprint(f"Input: {url_}")
        type_, id_ = find_id(url_)
        out = f"Output:{type_}, {id_}"
        if type_ == '[Failed]':
            out = f"[red]{out}[/red]"
        rprint(out)
        rprint("Time taken:", time() - start_time)
        rprint("-" * 50)

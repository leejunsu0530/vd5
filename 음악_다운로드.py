from VD4 import VideosManager, Videos, print_code, ask, formatstr, con  # type: ignore


stel = VideosManager(
         Videos(
      "https://www.youtube.com/playlist?list=PLLjd981H8qSN9PQ8-X6wINqBF1GjGxusy",
      inner_folder_split="%(uploader)s",
      artist_name="%(uploader)s",

         ),  # 스텔 커버곡
         Videos(
      "https://www.youtube.com/playlist?list=PLLjd981H8qSMGC4Nir0hD2Gj9n9PDUoHX",
      inner_folder_split="%(uploader)s",
      artist_name="%(uploader)s",
         ),  # 오리곡
    #     "https://www.youtube.com/@hebich",  # hebi.
    "https://www.youtube.com/playlist?list=PL6IyOjey3U8WiUwXw-1AIDv99qMB9otjp", # 무메이
    "https://www.youtube.com/playlist?list=PLcPAszg2ItaGAkxKIUiTTtgekfmgMmmEQ", # 벨즈
    "https://www.youtube.com/playlist?list=PLMUtkfkYDjAFJlZeDBNLAlrKjfue2DRRu",  # 미오
    "https://www.youtube.com/playlist?list=PLWGY2acU-ZeTnH4EvPHYEcqCUx145dDUP",  # 폴카
    "https://www.youtube.com/playlist?list=PLIGXZ2pMSuCGIcdF0iIZAqRAfsrYF9vvG",  # 리글로스 3d
    "https://www.youtube.com/playlist?list=PLIGXZ2pMSuCHOIswzCaJ7xrsTbohvHN8c",  # 리글로스 mv
    "https://www.youtube.com/playlist?list=PLIGXZ2pMSuCFTe7TQ7zigLqxfqc3L28h0",  # 리글로스 커버
    "https://www.youtube.com/playlist?list=PLrBvNRV0_lXKBnl9JI5sjYeGSKRU4SgHL",  # 플로우글로우 노래해봤다
    "https://www.youtube.com/playlist?list=PLrBvNRV0_lXJ-3BU1ZQVs1M5mj7NzbQ-y",  # 플로우글로우 mv
    "https://www.youtube.com/playlist?list=PLUfQ3xz0-Jen7EoEDeZAkl5yVuBdtw-Wl",  # 이로하 솔로
    "https://www.youtube.com/playlist?list=PLUfQ3xz0-JemBHsJIHPvt0ZTb7YpuwzYm",  # 이로하 콜라보
    "https://www.youtube.com/playlist?list=PLAo9RlHR2tDakgakxbOxT9dAZD0rpwvXQ",  # 스이 커버
    "https://www.youtube.com/playlist?list=PLAo9RlHR2tDZwddeEyp9nTfpaFB58DrXd",  # 스이 뮤비
    "https://www.youtube.com/playlist?list=PLAo9RlHR2tDZRNIVsqxS3U8kTgyROY1Xg",  # 스이 콜라보
    "https://www.youtube.com/playlist?list=PLUp1t9SPBl6qZQ3TLBIYYBbJwCQRzjgdc",  # 아쿠아 맨헤라?
    "https://www.youtube.com/playlist?list=PLUp1t9SPBl6rKXX4uAYsmEZyBlGwKE6Tl",  # 아쿠아 오리곡
    "https://www.youtube.com/playlist?list=PLUp1t9SPBl6qrPT_W79HOeR6_n-hWsAbk",  # 아쿠아 콜라보
    "https://www.youtube.com/playlist?list=PLUp1t9SPBl6r4nqsQBg7HH7fPX2l9AGQk",  # 아쿠아 노래해봤다
    "https://www.youtube.com/playlist?list=PLpt61bADOMwW2aA9I1hWHyR8OixSuCXzc",  # 아즈키 오리곡
#    "https://www.youtube.com/playlist?list=PLi6TWx3pTf1fVyYNxUCKNHmmssZjKnK9K",  # 사카마타 오리곡
    "https://www.youtube.com/playlist?list=PL_0A0t0-Y0ANo9NZV4LRSUzIus8JkmHEK",  # 소라 오리곡
    "https://www.youtube.com/playlist?list=PLzYaEBSRCCt7NBwVsrOHKNWe6Z2ym0gNO",  # 시온 오리곡
    "https://www.youtube.com/playlist?list=PLpt61bADOMwXIZpLr09sCNeocN7CXjcoS",  # 아즈키 커버
#    "https://www.youtube.com/playlist?list=PLi6TWx3pTf1dHW-DvMpPEW2NLDICBkW8z",  # 사카마타 노래해보았다
    "https://www.youtube.com/playlist?list=PL_0A0t0-Y0AMGFPCuKDZ3o8PMVpKcNvOQ",  # 소라 노래해보았다
    "https://www.youtube.com/playlist?list=PLzYaEBSRCCt5kgnBdQkLM7yDDZt2_NIZG",  # 시온 커버
    "https://www.youtube.com/playlist?list=PLIHyIgRAWkUz3MAUPbTg9XcuP_rzDJ1bk",  # 토와
    "https://www.youtube.com/playlist?list=PLD992QYJ2953ekTB3YuoHcF505PWPXlwb",  # 루이
    "https://www.youtube.com/playlist?list=PL6qjLH_5VIDUEA7yBOKxdRPdI4vYmL-dR&si=q0TlvAZA7x2lcw2-",  # 카나데
    "https://www.youtube.com/playlist?list=PL3y-e0n6k6gDoG3mViEOESGV1WhY8aCrR",  # 오카유
    "https://www.youtube.com/playlist?list=PLNvxSJodVoAu5ABQjfuPGnzqkRMLtN0y2",  # 카나타


    parent_videos_dir="C:\\Users\\user\\Desktop\\음악 정보 폴더",
    # parent_file_dir=,
)

# stel.show_total_info()
# ask.ask_continue("전체 표를 출력하시겠습니까?")
stel.show_total_table([
    'title',
    "playlist",
    "uploader",
    ('upload_date', formatstr.date)],
    # restrict=lambda d: d.get("is_downloaded")
)


# answer = ask.ask_choice(
# "어떤 방식으로 다운로드 하시겠습니까?",
# ["영상 파일", "음악 파일", "다운로드 안함"],
# "다운로드 안함",
# )
# if answer == "영상 파일":
# stel.download_as_video()
# elif answer == "음악 파일":
if ask.ask_y_or_n("음악 다운로드 하시겠습니까?"):
    stel.download_as_music()
# else:
# pass

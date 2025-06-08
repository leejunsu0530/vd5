from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    SpinnerColumn,
)
from .rich_vd4 import my_console


def progress_video_info() -> Progress:
    return Progress(
        TextColumn(
            "[bright_cyan]{task.description}[/] "
            "[bold bright_magenta]{task.fields[channel_name]}[/] "
            "[bold #ff5c00]{task.fields[playlist_title]}[/] "
            "[bold #ffc100]{task.fields[video_title]}",
            justify="left",
        ),
        # 현재 비디오 제목 표시
        BarColumn(
            style="dim cyan",  # 진행되지 않은(배경) 부분: 어두운 자홍
            complete_style="bright_cyan",  # 진행된(채워진) 부분: 시안
            finished_style="bold #03ff00",  # 작업 완료 시 전체 진행바: 밝은 연두색
            pulse_style="dim white",  # 펄스 애니메이션 시: 어두운 하얀색
        ),
        TextColumn("{task.percentage:>3.1f}%"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        SpinnerColumn(),
        console=my_console,
    )


def progress_playlist_data() -> Progress:
    """사라지게 하는 설정 필요, 메시지 수정은 부르는 쪽에서"""
    return Progress(
        TextColumn(
            "[bright_white]{task.description}[/]",
            justify="left"
        ),
        "(", TimeElapsedColumn(), "경과)",
        SpinnerColumn("simpleDots"),
        console=my_console,
    )

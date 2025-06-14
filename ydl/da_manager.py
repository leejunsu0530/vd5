from ..filemanage.filesave import read_str_from_file


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

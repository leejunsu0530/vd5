import os


def list_all_files(root_dir: str, ext: str | None = None) -> list[str]:
    """
    root_dir 내부의 모든 파일 경로를 반환.
    extensions가 주어지면, 해당 확장자들만 포함시킴.

    :param root_dir: 탐색할 루트 디렉토리
    :param ext: 포함할 확장자 리스트 (예: ['.txt', '.py'])
    :return: 파일 경로 리스트
    """
    all_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if ext is None or os.path.splitext(filename)[1].lower() in ext:
                full_path = os.path.join(dirpath, filename)
                all_files.append(full_path)
    return all_files


if __name__ == '__main__':
    from rich.pretty import pprint
    pprint(list_all_files(r"C:\Users\user\Desktop\음악 정보 폴더\Errors"))

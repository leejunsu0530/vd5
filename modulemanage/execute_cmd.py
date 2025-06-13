import subprocess
import shlex
from typing import Callable
import os


def execute_cmd(command: str) -> str:
    """
    Executes a shell command using subprocess and returns its output.
    If the command fails, it returns the error message.
    """
    # cmd = shlex.split(command)
    try:
        # Run the command, capturing both stdout and stderr
        result = subprocess.run(
            # cmd,
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()  # Return standard output if successful
    except subprocess.CalledProcessError as e:
        # Return error message if the command execution fails
        return f"Error: {e.stderr.strip()}"


def execute_cmd_realtime(command: str, print_: Callable = print, print_kwargs: dict = None, wait: bool = True):
    """run보다 복잡하고 많은 기능을 제공하는 popen 기능 사용
    Args:
        command: 실행할 명령어 문자열
        print_: 출력 함수. 필요시 rich의 console.print로 변경
        print_kwargs: print_에 전달할 인자 목록. rich를 쓸때의 {highlight: True} 등. 없는거 전달달하면 에러나니 주의
        wait: false로 하면 명령어가 끝나는 걸 기다리지 않고 다음 파이썬 구문으로 넘어감
    """
    process = None
    # cmd = shlex.split(command) # 이건 대괄호 들어간 문자열 깨짐
    if print_kwargs is None:
        print_kwargs = {}

    program, left_command = command.split(" ", 1)
    print(f"Command: \033[33m{program}\033[0m {left_command}")

    try:
        process = subprocess.Popen(
            # cmd,
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # 버퍼링 방식 지정. 1줄씩 출력에 필요
        )

        if process.stdout is None:
            raise RuntimeError("stdout을 가져오지 못했습니다.")

        # Popen이 성공했을 때만 stdout 읽기
        for line in iter(process.stdout.readline, ''):
            print_(line.rstrip(), **print_kwargs)

    except Exception:
        # Popen은 성공했는데 실행 중 에러 발생 시 생성된 서브프로세스 종료
        if process:
            process.terminate()
        raise  # 예외 다시 발생

    finally:
        if process and wait:
            process.wait()

# def execute_yt_dlp(command: str):
#     execute_cmd("yt-dlp" + command)

# def execute_idle():
#     execute_cmd("python -m idlelib")


if __name__ == "__main__":
    from rich.console import Console
    con = Console()
    execute_cmd_realtime("pip install yt-dlp", con.print, {"highlight": True})

from setuptools import setup, find_packages
# 이건 한 폴더 밖에서 해야 함
setup(
    name="VD4",  # Replace with your package name
    version="1.1.0",  # Initial release version
    author="Lee Junsu",
    description="Sort, filter and Download youtube playlist/channel's videos",
    packages=find_packages(exclude="time_check.py"),
    python_requires=">=3.11",
    install_requires=[
        # List your package dependencies here
        "extcolors",
        "yt-dlp[default,curl-cffi]",
        "rich",
        "requests",
    ],
)

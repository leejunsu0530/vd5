import sys

if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("가상환경 안에서 실행 중입니다")
else:
    print("!!가상환경 밖에서 실행 중입니다!!")

# 이게 왜 안되냐 그냥 콘다 쓸까

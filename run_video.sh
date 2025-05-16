#!/bin/bash
# 기본 비디오 생성 예제 실행

echo "✨ 기본 비디오 생성 예제 실행"
echo "프롬프트: $*"

if [ $# -eq 0 ]; then
    # 기본값 사용
    ./generate_video.py
else
    # 명령줄 인수로 전달된 프롬프트 사용
    ./generate_video.py --prompt "$*"
fi

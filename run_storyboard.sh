#!/bin/bash
# 스토리보드 기반 비디오 생성 예제 실행

echo "✨ 스토리보드 기반 비디오 생성 예제 실행"

# 스토리보드 디렉토리 확인
if [ -d "$1" ]; then
    echo "스토리보드 디렉토리: $1"
    ./generate_video_with_storyboard.py --storyboard-dir "$1"
else
    echo "기본 프롬프트로 스토리보드 생성 후 비디오 생성"
    ./generate_video_with_storyboard.py
fi

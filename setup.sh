#!/bin/bash
# 출력 디렉토리 생성
mkdir -p output

# 실행 권한 부여
chmod +x generate_video.py
chmod +x generate_video_with_storyboard.py
chmod +x handle_errors.py
chmod +x simple_example.py
chmod +x config.py
chmod +x check_config.py
chmod +x run_video.sh
chmod +x run_storyboard.sh

# .env 파일 생성 (있는 경우 백업)
if [ -f ".env" ]; then
    echo "기존 .env 파일을 백업합니다..."
    cp .env .env.backup
fi

# .env.example이 존재하면 복사
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo ".env 파일을 생성합니다..."
    cp .env.example .env
    echo "생성된 .env 파일을 편집하여 AWS 자격 증명을 설정하세요."
fi

echo "설정을 확인합니다..."
python check_config.py

echo "실행 권한이 부여되었습니다."
echo "예제를 실행하려면 다음 명령어를 사용하세요:"
echo "./run_video.sh '프롬프트'     - 기본 비디오 생성"
echo "./run_storyboard.sh       - 스토리보드 기반 비디오 생성"
echo "./simple_example.py       - 간단한 비디오 생성 예제"

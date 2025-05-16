# Amazon Bedrock 비디오 생성(Video Generation) 샘플

이 프로젝트는 Amazon Bedrock을 사용하여 비디오를 생성하는 기본 예제를 제공합니다.

## 사전 요구 사항

- AWS 계정
- Amazon Bedrock에 대한 액세스 권한
- Python 3.9+
- 필요 패키지 (requirements.txt 참조)

## 설치

```bash
# 필요 패키지 설치
pip install -r requirements.txt

# 개발 환경 설정 (실행 권한 부여, .env 파일 생성)
./setup.sh
```

## AWS 자격 증명 설정

### 방법 1: .env 파일 사용 (권장)

```bash
# .env 파일을 편집하여 AWS 자격 증명 설정
vi .env
```

또는 원하는 텍스트 편집기로 .env 파일을 편집하여 다음 설정을 입력합니다:

```
# AWS 자격 증명
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1  # 사용할 AWS 리전

# 비디오 생성 설정
DEFAULT_MODEL_ID=amazon.nova.video-1080p
DEFAULT_DURATION=5000
DEFAULT_IMAGE_QUALITY=standard
```

### 방법 2: 환경 변수 사용

```bash
# 환경 변수로 AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_REGION=<your-region>  # 예: us-east-1, us-west-2 등
```

## 사용 방법

1. 기본 비디오 생성:
   ```bash
   python generate_video.py
   ```

3. 스토리보드 기반 비디오 생성:
   ```bash
   python generate_video_with_storyboard.py
   ```

## 주요 파일

- `generate_video.py`: 기본 비디오 생성 예제
- `generate_video_with_storyboard.py`: 스토리보드 기반 비디오 생성 예제
- `handle_errors.py`: 오류 처리 예제

## 참고 자료

- [비디오 생성 액세스](https://docs.aws.amazon.com/nova/latest/userguide/video-gen-access.html)
- [비디오 생성 오류](https://docs.aws.amazon.com/nova/latest/userguide/video-gen-errors.html)
- [비디오 생성 코드 예제](https://docs.aws.amazon.com/nova/latest/userguide/video-gen-code-examples.html)
- [비디오 생성 코드 예제 2](https://docs.aws.amazon.com/nova/latest/userguide/video-gen-code-examples2.html)
- [비디오 생성 스토리보드](https://docs.aws.amazon.com/nova/latest/userguide/video-generation-storyboard.html)

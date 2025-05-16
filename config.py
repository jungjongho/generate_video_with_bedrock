#!/usr/bin/env python3
"""
환경 변수 설정 및 설정 관리 모듈
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.absolute()

# .env 파일 경로
ENV_FILE = PROJECT_ROOT / '.env'

# .env 파일이 존재하면 로드
if os.path.exists(ENV_FILE):
    logger.info(f"환경 변수 파일 로드 중: {ENV_FILE}")
    load_dotenv(ENV_FILE)
else:
    logger.warning(f".env 파일을 찾을 수 없습니다: {ENV_FILE}")
    logger.warning("환경 변수를 직접 설정하거나 .env 파일을 만드세요.")
    logger.warning("예시 파일 복사: cp .env.example .env")

# AWS 자격 증명 환경 변수
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# 비디오 생성 설정
DEFAULT_MODEL_ID = os.environ.get('DEFAULT_MODEL_ID', 'amazon.nova.video-1080p')
DEFAULT_DURATION = int(os.environ.get('DEFAULT_DURATION', 5000))
DEFAULT_IMAGE_QUALITY = os.environ.get('DEFAULT_IMAGE_QUALITY', 'standard')

# 출력 디렉토리
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', os.path.join(PROJECT_ROOT, 'output'))

def validate_aws_credentials():
    """AWS 자격 증명이 설정되어 있는지 확인합니다."""
    missing_vars = []
    
    if not AWS_ACCESS_KEY_ID:
        missing_vars.append('AWS_ACCESS_KEY_ID')
    
    if not AWS_SECRET_ACCESS_KEY:
        missing_vars.append('AWS_SECRET_ACCESS_KEY')
    
    if missing_vars:
        logger.warning(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.warning("AWS 자격 증명을 설정하려면 .env 파일을 만들거나 환경 변수를 직접 설정하세요.")
        return False
    
    return True

def create_boto3_session():
    """AWS 자격 증명으로 boto3 세션을 생성합니다."""
    import boto3
    
    # 환경 변수에서 자격 증명 가져오기
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    return session

def create_bedrock_client():
    """환경 변수의 자격 증명으로 Amazon Bedrock 클라이언트를 생성합니다."""
    if not validate_aws_credentials():
        logger.warning("AWS 자격 증명이 없어 기본 자격 증명 공급자 체인을 사용합니다.")
        # AWS 자격 증명이 없으면 기본 자격 증명 공급자 체인을 사용
        import boto3
        return boto3.client('bedrock-runtime', region_name=AWS_REGION)
    
    # 세션에서 클라이언트 생성
    session = create_boto3_session()
    return session.client('bedrock-runtime')

def print_config():
    """현재 설정을 출력합니다."""
    logger.info("=== 현재 설정 ===")
    logger.info(f"AWS 리전: {AWS_REGION}")
    logger.info(f"기본 모델 ID: {DEFAULT_MODEL_ID}")
    logger.info(f"기본 비디오 지속 시간: {DEFAULT_DURATION}ms")
    logger.info(f"기본 이미지 품질: {DEFAULT_IMAGE_QUALITY}")
    logger.info(f"출력 디렉토리: {OUTPUT_DIR}")
    
    # AWS 자격 증명 상태 확인
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        logger.info("AWS 자격 증명: 설정됨")
    else:
        logger.warning("AWS 자격 증명: 설정되지 않음")

if __name__ == "__main__":
    # 독립 실행 시 설정 정보 출력
    print_config()
    
    # AWS 자격 증명 유효성 검사
    validate_aws_credentials()

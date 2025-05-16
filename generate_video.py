#!/usr/bin/env python3
# chmod +x generate_video.py
"""
기본 Amazon Bedrock 비디오 생성 예제
"""

import json
import time
import uuid
import argparse
import boto3
import requests
from PIL import Image
import io
import os
import logging
from config import DEFAULT_MODEL_ID, DEFAULT_DURATION, OUTPUT_DIR, AWS_REGION, create_bedrock_client

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description='Amazon Bedrock 비디오 생성 예제')
    parser.add_argument('--prompt', type=str, default='A cat playing with a ball in a sunny garden',
                        help='비디오 생성을 위한 프롬프트')
    parser.add_argument('--model-id', type=str, default=DEFAULT_MODEL_ID,
                        help='사용할 Bedrock 모델 ID')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help='생성된 비디오와 이미지를 저장할 디렉토리')
    parser.add_argument('--region', type=str, default=AWS_REGION,
                        help='AWS 리전')
    
    return parser.parse_args()

def create_bedrock_client(region):
    """구성파일에서 Amazon Bedrock 클라이언트를 생성합니다."""
    # 리전이 지정되면 해당 리전 사용, 그렇지 않으면 환경 변수에서 로드
    if region != AWS_REGION:
        return boto3.client('bedrock-runtime', region_name=region)
    else:
        # 환경 변수에서 자격 증명 및 리전 로드
        from config import create_bedrock_client as load_client
        return load_client()

def generate_video(client, prompt, model_id):
    """Amazon Bedrock을 사용하여 비디오를 생성합니다."""
    
    # 요청 본문 생성
    request_body = {
        "modelId": model_id,
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps({
            "prompt": prompt,
            "seed": abs(hash(str(uuid.uuid4()))) % (2**32),  # 랜덤 시드
            "duration": 4000,  # 밀리초 단위의 지속 시간 (4초)
            "aspectRatio": "16:9",  # 비디오 비율 (16:9 표준)
            "jobType": "video-generation",
            "taskType": "text-to-video",
            "imageQuality": "standard",  # 고품질은 "premium"
            # 선택적 매개변수:
            # "negativePrompt": "poor quality, blurry, bad",
            # "initialImages": [...],  # 초기 이미지
            # "stylePreset": "photographic",  # 스타일 프리셋
        })
    }
    
    # API 호출 생성
    response = client.invoke_model(**request_body)
    response_body = json.loads(response['body'].read())
    
    return response_body

def download_content(url, output_path):
    """URL에서 콘텐츠를 다운로드하여 지정된 경로에 저장합니다."""
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    return output_path

def poll_job_status(client, job_id, model_id, interval=5, max_attempts=60):
    """작업 상태를 확인하고 완료될 때까지 폴링합니다."""
    
    attempts = 0
    while attempts < max_attempts:
        request_body = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "jobId": job_id,
                "taskType": "text-to-video"
            })
        }
        
        response = client.invoke_model(**request_body)
        response_body = json.loads(response['body'].read())
        
        status = response_body.get('status')
        logger.info(f"Job status: {status}")
        
        if status == 'completed':
            return response_body
        elif status in ['failed', 'expired']:
            raise Exception(f"Job {job_id} {status}: {response_body.get('errorMessage', 'No error message')}")
        
        time.sleep(interval)
        attempts += 1
    
    raise TimeoutError(f"Job {job_id} did not complete within the expected time")

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Bedrock 클라이언트 생성
    client = create_bedrock_client(args.region)
    
    try:
        # 비디오 생성 요청
        logger.info(f"비디오 생성 시작: '{args.prompt}'")
        response = generate_video(client, args.prompt, args.model_id)
        
        # 작업 ID 가져오기
        job_id = response.get('jobId')
        if not job_id:
            raise ValueError("응답에서 작업 ID를 찾을 수 없습니다")
        
        logger.info(f"작업 ID: {job_id}, 생성 상태 확인 중...")
        
        # 작업 상태 폴링
        result = poll_job_status(client, job_id, args.model_id)
        
        # 출력 결과 처리
        if 'videos' in result:
            video_url = result['videos'][0].get('url')
            if video_url:
                video_path = os.path.join(args.output_dir, f"video_{job_id}.mp4")
                download_content(video_url, video_path)
                logger.info(f"비디오가 성공적으로 생성되어 {video_path}에 저장되었습니다")
        
        # 썸네일 저장 (있는 경우)
        if 'thumbnails' in result:
            thumbnail_url = result['thumbnails'][0].get('url')
            if thumbnail_url:
                thumbnail_path = os.path.join(args.output_dir, f"thumbnail_{job_id}.jpg")
                download_content(thumbnail_url, thumbnail_path)
                logger.info(f"썸네일이 {thumbnail_path}에 저장되었습니다")
        
        logger.info("비디오 생성 완료!")
        
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

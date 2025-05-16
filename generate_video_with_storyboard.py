#!/usr/bin/env python3
# chmod +x generate_video_with_storyboard.py
"""
스토리보드 기반 Amazon Bedrock 비디오 생성 예제
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
import base64
import logging
from config import DEFAULT_MODEL_ID, DEFAULT_DURATION, OUTPUT_DIR, AWS_REGION, create_bedrock_client

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description='스토리보드 기반 Amazon Bedrock 비디오 생성 예제')
    parser.add_argument('--prompts', type=str, nargs='+', 
                        default=[
                            'A cat waking up in a sunny room',
                            'The cat stretches and yawns',
                            'The cat walks to the window',
                            'The cat looks outside at birds flying'
                        ],
                        help='스토리보드 씬을 위한 프롬프트 목록')
    parser.add_argument('--model-id', type=str, default=DEFAULT_MODEL_ID,
                        help='사용할 Bedrock 모델 ID')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help='생성된 비디오와 이미지를 저장할 디렉토리')
    parser.add_argument('--region', type=str, default=AWS_REGION,
                        help='AWS 리전')
    parser.add_argument('--storyboard-dir', type=str, default=None,
                        help='기존 이미지를 스토리보드로 사용할 경로 (선택 사항)')
    
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

def encode_image(image_path):
    """이미지를 Base64로 인코딩합니다."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_storyboard_images(client, prompts, model_id, output_dir):
    """프롬프트 목록에서 스토리보드 이미지를 생성합니다."""
    
    storyboard_images = []
    storyboard_dir = os.path.join(output_dir, "storyboard")
    os.makedirs(storyboard_dir, exist_ok=True)
    
    # 이미지 생성 모델 ID - 텍스트에서 이미지 모델 사용
    image_model_id = "stability.stable-diffusion-xl-v1"
    
    for i, prompt in enumerate(prompts):
        # 이미지 생성 요청
        request_body = {
            "modelId": image_model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "seed": abs(hash(prompt + str(uuid.uuid4()))) % (2**32),
                "steps": 30,
                "width": 1024,
                "height": 576,  # 16:9 비율
            })
        }
        
        logger.info(f"스토리보드 이미지 {i+1}/{len(prompts)} 생성 중: '{prompt}'")
        
        response = client.invoke_model(**request_body)
        response_body = json.loads(response['body'].read())
        
        # 이미지 저장
        if 'artifacts' in response_body and len(response_body['artifacts']) > 0:
            image_data = base64.b64decode(response_body['artifacts'][0]['base64'])
            image_path = os.path.join(storyboard_dir, f"storyboard_{i+1:02d}.png")
            
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            storyboard_images.append(image_path)
            logger.info(f"스토리보드 이미지 저장됨: {image_path}")
        
        # API 속도 제한 방지를 위한 짧은 대기
        time.sleep(1)
    
    return storyboard_images

def generate_video_from_storyboard(client, storyboard_images, model_id):
    """스토리보드 이미지를 기반으로 비디오를 생성합니다."""
    
    # 이미지를 Base64로 인코딩
    encoded_images = [encode_image(img_path) for img_path in storyboard_images]
    
    # 요청 본문 생성
    request_body = {
        "modelId": model_id,
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps({
            "storyboard": [
                {"base64EncodedImage": img} for img in encoded_images
            ],
            "seed": abs(hash(str(uuid.uuid4()))) % (2**32),  # 랜덤 시드
            "duration": 6000,  # 밀리초 단위의 지속 시간 (6초)
            "aspectRatio": "16:9",  # 비디오 비율
            "jobType": "video-generation",
            "taskType": "image-to-video",
            "imageQuality": "standard",  # 고품질은 "premium"
            # 선택적 매개변수:
            # "negativePrompt": "poor quality, blurry, bad",
            # "stylePreset": "photographic",
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
                "taskType": "image-to-video"
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

def list_image_files(directory):
    """디렉토리에서 이미지 파일 목록을 반환합니다."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    image_files = []
    
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file_path)
            if ext.lower() in image_extensions:
                image_files.append(file_path)
    
    # 파일명으로 정렬 (숫자 순서로 처리)
    image_files.sort()
    return image_files

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Bedrock 클라이언트 생성
    client = create_bedrock_client(args.region)
    
    try:
        # 스토리보드 이미지 가져오기
        if args.storyboard_dir and os.path.isdir(args.storyboard_dir):
            # 기존 이미지 디렉토리 사용
            logger.info(f"기존 스토리보드 이미지 디렉토리 사용: {args.storyboard_dir}")
            storyboard_images = list_image_files(args.storyboard_dir)
            if not storyboard_images:
                raise ValueError(f"지정된 디렉토리에 이미지 파일이 없습니다: {args.storyboard_dir}")
        else:
            # 새 스토리보드 이미지 생성
            logger.info("프롬프트에서 스토리보드 이미지 생성 중...")
            storyboard_images = generate_storyboard_images(client, args.prompts, args.model_id, args.output_dir)
        
        # 스토리보드 이미지 개수 확인
        logger.info(f"스토리보드 이미지 {len(storyboard_images)}개로 비디오 생성 중...")
        
        # 스토리보드에서 비디오 생성
        response = generate_video_from_storyboard(client, storyboard_images, args.model_id)
        
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
                video_path = os.path.join(args.output_dir, f"video_storyboard_{job_id}.mp4")
                download_content(video_url, video_path)
                logger.info(f"비디오가 성공적으로 생성되어 {video_path}에 저장되었습니다")
        
        # 썸네일 저장 (있는 경우)
        if 'thumbnails' in result:
            thumbnail_url = result['thumbnails'][0].get('url')
            if thumbnail_url:
                thumbnail_path = os.path.join(args.output_dir, f"thumbnail_storyboard_{job_id}.jpg")
                download_content(thumbnail_url, thumbnail_path)
                logger.info(f"썸네일이 {thumbnail_path}에 저장되었습니다")
        
        logger.info("스토리보드 기반 비디오 생성 완료!")
        
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
# chmod +x simple_example.py
"""
Amazon Bedrock 비디오 생성 간단한 사용 예제
"""

import os
import logging
import argparse
from handle_errors import BedrockVideoClient, BedrockVideoGenerationError
from config import DEFAULT_MODEL_ID, DEFAULT_DURATION, OUTPUT_DIR, AWS_REGION

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description='Amazon Bedrock 비디오 생성 간단한 예제')
    parser.add_argument('--prompt', type=str,
                        default='A beautiful sunrise over mountains with birds flying',
                        help='비디오 생성을 위한 프롬프트')
    parser.add_argument('--model-id', type=str,
                        default=DEFAULT_MODEL_ID,
                        help='사용할 Bedrock 모델 ID')
    parser.add_argument('--duration', type=int, default=DEFAULT_DURATION,
                        help='비디오 지속 시간(밀리초)')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help='생성된 비디오를 저장할 디렉토리')
    parser.add_argument('--region', type=str, default=AWS_REGION,
                        help='AWS 리전')
    
    return parser.parse_args()

def download_video(url, output_path):
    """URL에서 비디오를 다운로드합니다."""
    import requests
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_path

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)
    
    # BedrockVideoClient 초기화
    client = BedrockVideoClient(region=args.region)
    
    try:
        # 1. 비디오 생성 요청
        logger.info(f"비디오 생성 시작: '{args.prompt}'")
        
        response = client.generate_video(
            prompt=args.prompt,
            model_id=args.model_id,
            duration=args.duration,
            image_quality="standard"
        )
        
        # 2. 작업 ID 가져오기
        job_id = response.get('jobId')
        if not job_id:
            raise ValueError("응답에서 작업 ID를 찾을 수 없습니다")
        
        logger.info(f"작업 ID: {job_id}, 생성 상태 확인 중...")
        
        # 3. 작업 완료 대기
        result = client.wait_for_job_completion(
            job_id=job_id,
            model_id=args.model_id,
            interval=5,
            max_attempts=60,
            timeout=300
        )
        
        # 4. 결과 처리
        if 'videos' in result and len(result['videos']) > 0:
            video_url = result['videos'][0].get('url')
            if video_url:
                video_path = os.path.join(args.output_dir, f"video_{job_id}.mp4")
                download_video(video_url, video_path)
                logger.info(f"비디오가 성공적으로 생성되어 {video_path}에 저장되었습니다")
            else:
                logger.warning("비디오 URL을 찾을 수 없습니다")
        else:
            logger.warning("생성된 비디오가 없습니다")
        
        # 5. 썸네일 처리 (있는 경우)
        if 'thumbnails' in result and len(result['thumbnails']) > 0:
            thumbnail_url = result['thumbnails'][0].get('url')
            if thumbnail_url:
                thumbnail_path = os.path.join(args.output_dir, f"thumbnail_{job_id}.jpg")
                download_video(thumbnail_url, thumbnail_path)
                logger.info(f"썸네일이 {thumbnail_path}에 저장되었습니다")
        
        logger.info("비디오 생성 완료!")
        
    except BedrockVideoGenerationError as e:
        logger.error(f"비디오 생성 오류: {str(e)}")
        return 1
    except ValueError as e:
        logger.error(f"값 오류: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
# chmod +x handle_errors.py
"""
Amazon Bedrock 비디오 생성 에러 처리 예제
"""

import json
import time
import boto3
import logging
from botocore.exceptions import ClientError
from config import create_bedrock_client, AWS_REGION

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BedrockVideoGenerationError(Exception):
    """Amazon Bedrock 비디오 생성 관련 예외 클래스"""
    pass

def handle_common_errors(func):
    """Amazon Bedrock API 호출 시 일반적인 오류를 처리하는 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_msg = e.response.get('Error', {}).get('Message')
            
            # 일반적인 AWS 오류 처리
            if error_code == 'AccessDeniedException':
                logger.error(f"액세스 거부됨: {error_msg}. IAM 권한을 확인하세요.")
                raise BedrockVideoGenerationError(f"액세스 권한 오류: {error_msg}")
            elif error_code == 'ValidationException':
                logger.error(f"유효성 검사 오류: {error_msg}. 요청 매개변수를 확인하세요.")
                raise BedrockVideoGenerationError(f"유효성 검사 오류: {error_msg}")
            elif error_code == 'ResourceNotFoundException':
                logger.error(f"리소스를 찾을 수 없음: {error_msg}. 모델 ID와 엔드포인트를 확인하세요.")
                raise BedrockVideoGenerationError(f"리소스를 찾을 수 없음: {error_msg}")
            elif error_code == 'ThrottlingException':
                logger.error(f"요청이 제한됨: {error_msg}. 재시도하거나 API 호출 빈도를 줄이세요.")
                raise BedrockVideoGenerationError(f"요청 제한 오류: {error_msg}")
            elif error_code == 'ServiceQuotaExceededException':
                logger.error(f"서비스 할당량 초과: {error_msg}. AWS 콘솔에서 할당량 증가를 요청하세요.")
                raise BedrockVideoGenerationError(f"할당량 초과 오류: {error_msg}")
            else:
                logger.error(f"AWS API 오류 발생: {error_code} - {error_msg}")
                raise BedrockVideoGenerationError(f"AWS API 오류: {error_code} - {error_msg}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 디코딩 오류: {str(e)}. 응답이 올바른 JSON 형식인지 확인하세요.")
            raise BedrockVideoGenerationError(f"JSON 디코딩 오류: {str(e)}")
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            raise BedrockVideoGenerationError(f"예상치 못한 오류: {str(e)}")
    
    return wrapper

class BedrockVideoClient:
    """Amazon Bedrock 비디오 생성 API를 위한 래퍼 클래스"""
    
    def __init__(self, region=None):
        """Amazon Bedrock 클라이언트 초기화"""
        # region 매개변수가 제공되면 사용, 그렇지 않으면 config.py의 AWS_REGION 사용
        if region:
            self.client = boto3.client('bedrock-runtime', region_name=region)
        else:
            # 환경 변수에서 자격 증명 및 리전 로드
            self.client = create_bedrock_client()
    
    @handle_common_errors
    def generate_video(self, prompt, model_id='amazon.nova.video-1080p', **kwargs):
        """텍스트 프롬프트에서 비디오 생성 요청"""
        
        # 필수 매개변수 검증
        if not prompt or not isinstance(prompt, str):
            raise ValueError("유효한 텍스트 프롬프트가 필요합니다")
        
        # 기본 매개변수 설정
        body = {
            "prompt": prompt,
            "seed": kwargs.get('seed', 42),
            "duration": kwargs.get('duration', 4000),  # 밀리초 단위 (기본값 4초)
            "aspectRatio": kwargs.get('aspect_ratio', "16:9"),
            "jobType": "video-generation",
            "taskType": "text-to-video",
            "imageQuality": kwargs.get('image_quality', "standard"),
        }
        
        # 선택적 매개변수 추가
        if 'negative_prompt' in kwargs:
            body['negativePrompt'] = kwargs['negative_prompt']
        
        if 'style_preset' in kwargs:
            body['stylePreset'] = kwargs['style_preset']
        
        # 요청 본문 생성
        request_body = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps(body)
        }
        
        # API 호출
        try:
            response = self.client.invoke_model(**request_body)
            response_body = json.loads(response['body'].read())
            return response_body
        except Exception as e:
            logger.error(f"비디오 생성 요청 중 오류 발생: {str(e)}")
            raise
    
    @handle_common_errors
    def check_job_status(self, job_id, model_id='amazon.nova.video-1080p', task_type='text-to-video'):
        """비디오 생성 작업 상태 확인"""
        
        if not job_id or not isinstance(job_id, str):
            raise ValueError("유효한 작업 ID가 필요합니다")
            
        request_body = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "jobId": job_id,
                "taskType": task_type
            })
        }
        
        try:
            response = self.client.invoke_model(**request_body)
            response_body = json.loads(response['body'].read())
            
            status = response_body.get('status')
            if status == 'failed':
                error_message = response_body.get('errorMessage', '알 수 없는 오류')
                logger.error(f"비디오 생성 작업 실패: {error_message}")
                raise BedrockVideoGenerationError(f"비디오 생성 작업 실패: {error_message}")
            
            return response_body
        except Exception as e:
            logger.error(f"작업 상태 확인 중 오류 발생: {str(e)}")
            raise
    
    @handle_common_errors
    def wait_for_job_completion(self, job_id, model_id='amazon.nova.video-1080p', task_type='text-to-video', 
                              interval=5, max_attempts=60, timeout=300):
        """비디오 생성 작업이 완료될 때까지 대기"""
        
        if not job_id:
            raise ValueError("유효한 작업 ID가 필요합니다")
        
        start_time = time.time()
        attempt = 0
        
        while attempt < max_attempts and (time.time() - start_time) < timeout:
            try:
                response = self.check_job_status(job_id, model_id, task_type)
                status = response.get('status')
                
                if status == 'completed':
                    logger.info(f"작업 {job_id} 완료됨")
                    return response
                elif status == 'failed':
                    error_message = response.get('errorMessage', '알 수 없는 오류')
                    raise BedrockVideoGenerationError(f"비디오 생성 작업 실패: {error_message}")
                elif status == 'expired':
                    raise BedrockVideoGenerationError("비디오 생성 작업이 만료되었습니다")
                
                logger.info(f"작업 상태: {status}, 대기 중... (시도 {attempt+1}/{max_attempts})")
                time.sleep(interval)
                attempt += 1
                
            except Exception as e:
                if isinstance(e, BedrockVideoGenerationError):
                    raise
                logger.error(f"작업 상태 확인 중 오류 발생: {str(e)}")
                time.sleep(interval)
                attempt += 1
        
        # 제한 시간 초과 또는 최대 시도 횟수 초과
        if (time.time() - start_time) >= timeout:
            raise TimeoutError(f"작업 {job_id}이(가) 제한 시간 {timeout}초 내에 완료되지 않았습니다")
        else:
            raise TimeoutError(f"작업 {job_id}이(가) 최대 시도 횟수 {max_attempts}회 내에 완료되지 않았습니다")

# 예제 사용법
def main():
    """에러 처리 예제 실행"""
    
    # 1. 클라이언트 초기화
    client = BedrockVideoClient(region='us-east-1')
    
    try:
        # 2. 비디오 생성 요청
        prompt = "A beautiful sunset over the ocean with waves crashing on the shore"
        response = client.generate_video(
            prompt=prompt,
            seed=12345,
            duration=5000,  # 5초
            image_quality="premium",
            negative_prompt="poor quality, blurry, distorted",
            style_preset="photographic"
        )
        
        # 3. 작업 ID 가져오기
        job_id = response.get('jobId')
        if not job_id:
            raise ValueError("응답에서 작업 ID를 찾을 수 없습니다")
        
        logger.info(f"비디오 생성 작업 ID: {job_id}")
        
        # 4. 작업 완료 대기
        result = client.wait_for_job_completion(
            job_id=job_id,
            interval=5,  # 5초 간격으로 상태 확인
            max_attempts=60,  # 최대 60회 시도
            timeout=300  # 최대 5분 대기
        )
        
        # 5. 결과 처리
        if result.get('status') == 'completed':
            if 'videos' in result and len(result['videos']) > 0:
                video_url = result['videos'][0].get('url')
                logger.info(f"생성된 비디오 URL: {video_url}")
            else:
                logger.warning("비디오 URL을 찾을 수 없습니다")
        
    except BedrockVideoGenerationError as e:
        logger.error(f"비디오 생성 오류: {str(e)}")
    except ValueError as e:
        logger.error(f"값 오류: {str(e)}")
    except TimeoutError as e:
        logger.error(f"시간 초과 오류: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    main()

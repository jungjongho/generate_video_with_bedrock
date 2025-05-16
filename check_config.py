#!/usr/bin/env python3
"""
현재 환경 변수 설정 및 AWS 자격 증명 상태를 확인합니다.
"""

from config import print_config, validate_aws_credentials

if __name__ == "__main__":
    print("\n=== Amazon Bedrock 비디오 생성 설정 확인 ===\n")
    
    # 설정 출력
    print_config()
    
    # AWS 자격 증명 확인
    if validate_aws_credentials():
        print("\n✅ AWS 자격 증명이 정상적으로 설정되어 있습니다.")
    else:
        print("\n❌ AWS 자격 증명이 설정되지 않았습니다.")
        print("  .env 파일을 편집하거나 환경 변수를 설정하세요.")
    
    print("\n프로젝트 준비가 완료되었습니다!")

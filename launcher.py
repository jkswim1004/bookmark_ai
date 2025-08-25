#!/usr/bin/env python3
"""
데이터 수집 웹 애플리케이션 런처
실행 파일(.exe)로 만들기 위한 메인 스크립트
"""
import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

def setup_environment():
    """실행 환경 설정"""
    # 실행 파일이 있는 디렉토리를 작업 디렉토리로 설정
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 실행 파일인 경우
        application_path = os.path.dirname(sys.executable)
    else:
        # 개발 환경에서 실행하는 경우
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    
    # uploads 폴더 생성
    uploads_dir = Path('uploads')
    uploads_dir.mkdir(exist_ok=True)
    
    return application_path

def open_browser():
    """3초 후 브라우저 자동 열기"""
    time.sleep(3)
    webbrowser.open('http://localhost:8080')

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 데이터 수집 웹 애플리케이션 시작")
    print("=" * 60)
    
    try:
        # 환경 설정
        app_path = setup_environment()
        print(f"📁 작업 디렉토리: {app_path}")
        
        # 브라우저 자동 열기 (백그라운드)
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Flask 애플리케이션 import 및 실행
        print("🔧 Flask 애플리케이션 로딩 중...")
        from application import application
        
        print("✅ 애플리케이션 로드 완료!")
        print("🌐 웹 서버 시작: http://localhost:8080")
        print("📱 잠시 후 브라우저가 자동으로 열립니다...")
        print("\n💡 종료하려면 Ctrl+C를 누르세요.")
        print("-" * 60)
        
        # Flask 앱 실행
        application.run(
            host='127.0.0.1',
            port=8080,
            debug=False,
            use_reloader=False  # 실행 파일에서는 reloader 비활성화
        )
        
    except ImportError as e:
        print(f"❌ 모듈 로드 오류: {e}")
        print("필요한 패키지가 설치되지 않았을 수 있습니다.")
        input("Enter 키를 눌러 종료하세요...")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자가 애플리케이션을 종료했습니다.")
        print("👋 안녕히 가세요!")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        input("Enter 키를 눌러 종료하세요...")
        sys.exit(1)

if __name__ == '__main__':
    main() 
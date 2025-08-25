import zipfile
import os

def create_release_package():
    """완전한 실행 패키지 생성 (사용자가 바로 실행할 수 있는 버전)"""
    
    # 실행에 필요한 모든 파일들
    files_to_include = [
        # 실행 파일들
        'run_app.bat',           # 메인 실행 파일 (더블클릭)
        'launcher.py',           # Python 런처
        
        # 핵심 애플리케이션 파일들
        'application.py',        # Flask 웹 앱
        'data_collector.py',     # 데이터 수집 모듈
        
        # 설정 파일들
        'requirements.txt',      # Python 패키지 목록
        'runtime.txt',           # Python 버전 지정
        '.gitignore',           # Git 설정 (참고용)
        
        # AWS 배포 관련 (선택사항)
        '.ebextensions/python.config',
        'deploy-hybrid-final-v2.zip',
        
        # 문서
        'README.md'
    ]
    
    # 추가로 생성할 파일들
    additional_files = {
        '사용법.txt': """
🚀 데이터 수집 웹 애플리케이션 사용법
========================================

📋 설치 및 실행:
1. 이 폴더를 원하는 위치에 압축 해제
2. "run_app.bat" 파일을 더블클릭
3. 자동으로 브라우저가 열리고 앱이 실행됩니다

🌐 접속 주소: http://localhost:8000

⚠️  주의사항:
- Python 3.8 이상이 설치되어 있어야 합니다
- 처음 실행 시 필요한 패키지를 자동으로 설치합니다
- 인터넷 연결이 필요합니다 (패키지 설치용)

🛠️ 문제 해결:
- Python이 없다면: https://python.org 에서 다운로드
- 실행 안 될 때: "launcher.py"를 Python으로 실행
- 포트 충돌 시: application.py에서 포트 번호 변경

📧 문의: GitHub 저장소 Issues 섹션 참고
""",
        
        '시스템 요구사항.txt': """
💻 시스템 요구사항
==================

🐍 Python: 3.8 이상
📦 필수 패키지:
- Flask 3.1.1
- pandas 2025.2  
- psutil (옵션, 로컬 데이터 수집용)

💾 디스크 공간: 최소 100MB
🌐 네트워크: 인터넷 연결 필요 (최초 설치 시)

✅ 지원 운영체제:
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+)

⚡ 권장 사양:
- RAM: 4GB 이상
- CPU: 듀얼코어 이상
"""
    }
    
    zip_filename = 'DataCollectorApp-Release.zip'
    
    print("📦 완전한 실행 패키지 생성 중...")
    print("=" * 50)
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 기본 파일들 추가
        for file_path in files_to_include:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f'✅ {file_path}')
            else:
                print(f'⚠️  {file_path} (파일 없음 - 건너뜀)')
        
        # 추가 문서 파일들 생성 및 추가
        for filename, content in additional_files.items():
            zipf.writestr(filename, content.strip())
            print(f'📝 {filename} (생성됨)')
        
        # uploads 폴더 구조 생성 (빈 폴더)
        zipf.writestr('uploads/.gitkeep', '# 데이터 파일이 저장되는 폴더')
        print(f'📁 uploads/ (폴더 구조 생성)')
    
    print("=" * 50)
    print(f'🎉 완성! 파일명: {zip_filename}')
    
    # 파일 크기 및 내용 확인
    file_size = os.path.getsize(zip_filename)
    print(f'📦 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)')
    
    print(f'\n📋 사용법:')
    print(f'1. {zip_filename} 파일을 원하는 위치에 압축 해제')
    print(f'2. "run_app.bat" 파일을 더블클릭하여 실행')
    print(f'3. 브라우저에서 http://localhost:8000 접속')
    
    return zip_filename

if __name__ == '__main__':
    create_release_package() 
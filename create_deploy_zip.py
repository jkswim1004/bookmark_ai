import zipfile
import os

def create_deployment_zip():
    """AWS 배포용 ZIP 파일 생성"""
    
    files_to_include = [
        'application.py',
        'data_collector.py', 
        'requirements.txt',
        'runtime.txt',
        '.ebextensions/python.config'
    ]
    
    zip_filename = 'deploy-hybrid-final-v2.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_include:
            if os.path.exists(file_path):
                # Linux 호환 경로로 저장
                arcname = file_path.replace('\\', '/')
                zipf.write(file_path, arcname)
                print(f'✅ 추가됨: {file_path} -> {arcname}')
            else:
                print(f'❌ 파일 없음: {file_path}')
    
    print(f'\n🎉 배포 파일 생성 완료: {zip_filename}')
    
    # 파일 크기 확인
    file_size = os.path.getsize(zip_filename)
    print(f'📦 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)')

if __name__ == '__main__':
    create_deployment_zip() 
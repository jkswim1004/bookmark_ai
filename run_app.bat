@echo off
title 데이터 수집 웹 애플리케이션
cls

echo ============================================================
echo 🚀 데이터 수집 웹 애플리케이션 시작
echo ============================================================
echo.

REM 가상환경이 있는지 확인
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.
)

REM uploads 폴더 생성
if not exist "uploads" (
    echo 📁 uploads 폴더 생성 중...
    mkdir uploads
)

echo 🔧 필요한 패키지 확인 중...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flask가 설치되어 있지 않습니다. 설치를 시작합니다...
    pip install flask pandas psutil
    if %errorlevel% neq 0 (
        echo ❌ 패키지 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

echo ✅ 환경 확인 완료!
echo 🌐 웹 서버 시작: http://localhost:8000
echo 📱 브라우저에서 위 주소로 접속하세요.
echo.
echo 💡 종료하려면 Ctrl+C를 누르세요.
echo ------------------------------------------------------------

REM 3초 후 브라우저 자동 열기 (백그라운드)
start /b timeout /t 3 >nul && start http://localhost:8000

REM Flask 애플리케이션 실행
python application.py

echo.
echo 👋 애플리케이션이 종료되었습니다.
pause 
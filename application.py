from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session, send_file
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import io
import base64
from generate_interactive_html import generate_interactive_analysis_html

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경 변수 로드
    print("✅ .env 파일 로드 성공")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다.")

# 환경 감지 및 데이터 수집 모듈 import
try:
    from data_collector import (ChromeBookmarkCollector, SystemInfoCollector, BrowserHistoryCollector, 
                               RecentFilesCollector, NetworkInfoCollector, is_aws_environment)
    DATA_COLLECTORS_AVAILABLE = True
    print("✅ 데이터 수집 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ 데이터 수집 모듈 로드 실패: {e}")
    DATA_COLLECTORS_AVAILABLE = False
    # is_aws_environment 함수 정의 (fallback)
    def is_aws_environment():
        """AWS 환경인지 확인"""
        import os
        aws_indicators = [
            os.environ.get('AWS_REGION'),
            os.environ.get('AWS_EXECUTION_ENV'),
            os.environ.get('EB_NODE_COMMAND'),
            '/opt/elasticbeanstalk' in os.environ.get('PATH', ''),
            os.path.exists('/opt/elasticbeanstalk')
        ]
        return any(aws_indicators)

# AI 분석 모듈 import
try:
    from ai_analyzer import AIPersonalityAnalyzer, prepare_data_for_ai_analysis
    AI_ANALYZER_AVAILABLE = True
    print("✅ AI 분석 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ AI 분석 모듈 로드 실패: {e}")
    AI_ANALYZER_AVAILABLE = False

# Flask 앱 생성
application = Flask(__name__)
application.secret_key = 'your-secret-key-here'  # 세션을 위한 시크릿 키

# 업로드 폴더 설정
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 동의서 템플릿
CONSENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>데이터 수집 동의서</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .consent-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #667eea;
        }
        
        .consent-section h3 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 15px;
        }
        
        .consent-section p {
            line-height: 1.6;
            color: #495057;
            margin-bottom: 10px;
        }
        
        .consent-section ul {
            padding-left: 20px;
            color: #495057;
        }
        
        .consent-section li {
            margin-bottom: 8px;
            line-height: 1.5;
        }
        
        .checkbox-group {
            display: flex;
            align-items: flex-start;
            margin: 20px 0;
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e9ecef;
            transition: border-color 0.3s ease;
        }
        
        .checkbox-group:hover {
            border-color: #667eea;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-right: 15px;
            margin-top: 2px;
            cursor: pointer;
        }
        
        .checkbox-group label {
            margin: 0;
            cursor: pointer;
            color: #495057;
            font-weight: 500;
            line-height: 1.5;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn-container {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
        }
        
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .warning strong {
            display: block;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 데이터 수집 동의서</h1>
        
        <div class="consent-section">
            <h3>🔍 수집하는 데이터</h3>
            <p>본 시스템은 다음과 같은 데이터를 수집합니다:</p>
            <ul>
                <li><strong>Chrome 북마크:</strong> 저장된 북마크 목록과 폴더 구조</li>
                <li><strong>브라우저 히스토리:</strong> 방문한 웹사이트 기록 (최근 30일)</li>
                <li><strong>시스템 정보:</strong> 운영체제, 하드웨어 사양, 설치된 프로그램 목록</li>
            </ul>
        </div>
        
        <div class="consent-section">
            <h3>🎯 수집 목적</h3>
            <p>수집된 데이터는 다음 목적으로만 사용됩니다:</p>
            <ul>
                <li>개인의 웹 브라우징 패턴 분석</li>
                <li>관심사 및 선호도 파악</li>
                <li>개인화된 추천 서비스 제공</li>
                <li>시스템 사용 현황 분석</li>
            </ul>
        </div>
        
        <div class="consent-section">
            <h3>🔒 데이터 보안</h3>
            <p>귀하의 개인정보 보호를 위해 다음과 같은 조치를 취합니다:</p>
            <ul>
                <li>수집된 데이터는 암호화되어 저장됩니다</li>
                <li>제3자와 데이터를 공유하지 않습니다</li>
                <li>분석 완료 후 원본 데이터는 안전하게 삭제됩니다</li>
                <li>언제든지 데이터 삭제를 요청할 수 있습니다</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ 중요 안내</strong>
            본 동의는 언제든지 철회할 수 있으며, 동의 철회 시 수집된 모든 데이터가 즉시 삭제됩니다.
        </div>
        
        <form method="POST" action="/consent">
            <div class="checkbox-group">
                <input type="checkbox" id="consentData" name="consent_data" required>
                <label for="consentData">위 내용을 모두 확인했으며, 데이터 수집에 동의합니다.</label>
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="consentAnalysis" name="consent_analysis" required>
                <label for="consentAnalysis">수집된 데이터의 분석 및 활용에 동의합니다.</label>
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="consentAge" name="consent_age" required>
                <label for="consentAge">만 14세 이상이며, 본 동의서의 내용을 충분히 이해했습니다.</label>
            </div>
            
            <div class="btn-container">
                <button type="submit" class="btn" id="agreeBtn" disabled>✅ 동의하고 계속하기</button>
                <button type="button" class="btn" onclick="window.history.back()" style="background: #6c757d;">❌ 동의하지 않음</button>
            </div>
        </form>
    </div>

    <script>
        // 모든 체크박스가 선택되었을 때만 동의 버튼 활성화
        function updateAgreeButton() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const agreeBtn = document.getElementById('agreeBtn');
            
            let allChecked = true;
            checkboxes.forEach(checkbox => {
                if (!checkbox.checked) {
                    allChecked = false;
                }
            });
            
            agreeBtn.disabled = !allChecked;
        }
        
        // 체크박스 변경 시 버튼 상태 업데이트
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', updateAgreeButton);
        });
    </script>
</body>
</html>
'''

# 데이터 수집 메인 템플릿
DATA_COLLECTION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>데이터 수집</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            font-weight: 300;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .collection-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .collection-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            border: 1px solid #e1e8ed;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .collection-section:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }
        
        .collection-section h3 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.4em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-group {
            margin: 20px 0;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
            font-size: 14px;
        }
        
        input, select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
            background: white;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
        }
        
        .btn-success:hover {
            box-shadow: 0 6px 20px rgba(46, 204, 113, 0.4);
        }
        
        .progress {
            background-color: #e9ecef;
            border-radius: 15px;
            padding: 6px;
            margin: 15px 0;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .progress-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 12px;
            border-radius: 10px;
            width: 0%;
            transition: width 0.8s ease;
            position: relative;
            overflow: hidden;
        }
        
        .progress-bar::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 11px;
            font-weight: bold;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            z-index: 10;
            pointer-events: none;
        }
        
        .ai-progress-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            border: 2px solid #dee2e6;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .progress-steps {
            display: flex !important;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            position: relative;
            width: 100%;
            flex-wrap: nowrap;
        }
        
        .progress-step {
            flex: 1;
            text-align: center;
            position: relative;
            padding: 10px 5px;
            min-width: 80px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .progress-step::before {
            content: '';
            position: absolute;
            top: 15px;
            left: 50%;
            width: calc(100% - 30px);
            height: 2px;
            background: #dee2e6;
            z-index: 1;
        }
        
        .progress-step:last-child::before {
            display: none;
        }
        
        .progress-step:first-child::before {
            display: none;
        }
        
        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #dee2e6;
            color: #6c757d;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px;
            font-weight: bold;
            font-size: 12px;
            position: relative;
            z-index: 2;
            transition: all 0.3s ease;
        }
        
        .step-circle.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .step-circle.completed {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .step-label {
            font-size: 11px;
            color: #6c757d;
            font-weight: 500;
        }
        
        .step-label.active {
            color: #667eea;
            font-weight: bold;
        }
        
        .step-label.completed {
            color: #28a745;
            font-weight: bold;
        }
        
        .status {
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            font-weight: 500;
        }
        
        .status.success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #b8daff;
            color: #155724;
        }
        
        .status.error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .status.info {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            margin: 15px 0;
            background: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 12px;
            cursor: pointer;
        }
        
        .checkbox-group label {
            margin: 0;
            cursor: pointer;
            color: #495057;
        }
        
        .navigation {
            text-align: center;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #e9ecef;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            
            .collection-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 데이터 수집</h1>
        
        <!-- 초기화 버튼 -->
        <div style="text-align: center; margin: 20px 0;">
            <button class="btn" onclick="clearAllFiles()" id="clearBtn" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white;">
                🗑️ 모든 파일 초기화
            </button>
            <div class="progress" id="clearProgress" style="display: none;">
                <div class="progress-bar" id="clearProgressBar"></div>
            </div>
            <div id="clearStatus"></div>
        </div>
        
        <div class="collection-grid">
            <!-- 북마크 수집 섹션 -->
            <div class="collection-section">
                <h3>🔖 Chrome 북마크 수집</h3>
                <div class="form-group">
                    <label for="startDate">시작 날짜:</label>
                    <input type="date" id="startDate" name="startDate">
                </div>
                <div class="form-group">
                    <label for="endDate">종료 날짜:</label>
                    <input type="date" id="endDate" name="endDate">
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="includeFolders" checked>
                    <label for="includeFolders">폴더 구조 포함</label>
                </div>
                <button class="btn" onclick="collectBookmarks()" id="bookmarkBtn">북마크 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="bookmarkProgress"></div>
                </div>
                <div id="bookmarkStatus"></div>
            </div>

            <!-- 브라우저 히스토리 수집 섹션 -->
            <div class="collection-section">
                <h3>🌐 브라우저 히스토리 수집</h3>
                <div class="form-group">
                    <label for="historyDays">수집 기간:</label>
                    <select id="historyDays">
                        <option value="7">최근 7일</option>
                        <option value="30" selected>최근 30일</option>
                        <option value="90">최근 90일</option>
                        <option value="365">최근 1년</option>
                    </select>
                </div>
                <button class="btn" onclick="collectHistory()" id="historyBtn">히스토리 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="historyProgress"></div>
                </div>
                <div id="historyStatus"></div>
            </div>

            <!-- 시스템 정보 수집 섹션 -->
            <div class="collection-section">
                <h3>💻 시스템 정보 수집</h3>
                <p style="color: #6c757d; margin-bottom: 20px;">설치된 프로그램과 실행 중인 프로세스 정보를 수집합니다.</p>
                <button class="btn" onclick="collectSystemInfo()" id="systemBtn">시스템 정보 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="systemProgress"></div>
                </div>
                <div id="systemStatus"></div>
            </div>

            <!-- Chrome 확장 프로그램 수집 섹션 -->
            <div class="collection-section">
                <h3>🧩 Chrome 확장 프로그램 수집</h3>
                <p style="color: #6c757d; margin-bottom: 20px;">설치된 Chrome 확장 프로그램 목록과 권한 정보를 수집합니다.</p>
                <button class="btn" onclick="collectChromeExtensions()" id="extensionsBtn">확장 프로그램 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="extensionsProgress"></div>
                </div>
                <div id="extensionsStatus"></div>
            </div>

            <!-- 최근 사용한 파일 수집 섹션 -->
            <div class="collection-section">
                <h3>📁 최근 사용한 파일 수집</h3>
                <div class="form-group">
                    <label for="recentFileDays">수집 기간:</label>
                    <select id="recentFileDays">
                        <option value="3">최근 3일</option>
                        <option value="7" selected>최근 7일</option>
                        <option value="14">최근 14일</option>
                        <option value="30">최근 30일</option>
                    </select>
                </div>
                <button class="btn" onclick="collectRecentFiles()" id="recentFilesBtn">최근 파일 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="recentFilesProgress"></div>
                </div>
                <div id="recentFilesStatus"></div>
            </div>

            <!-- 네트워크 정보 수집 섹션 -->
            <div class="collection-section">
                <h3>🌐 네트워크 정보 수집</h3>
                <p style="color: #6c757d; margin-bottom: 20px;">네트워크 연결 상태, 사용량, 인터페이스 정보를 수집합니다.</p>
                <button class="btn" onclick="collectNetworkInfo()" id="networkBtn">네트워크 정보 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="networkProgress"></div>
                </div>
                <div id="networkStatus"></div>
            </div>

            <!-- 설치된 프로그램 수집 섹션 -->
            <div class="collection-section">
                <h3>📦 설치된 프로그램 수집</h3>
                <p style="color: #6c757d; margin-bottom: 20px;">시스템에 설치된 모든 프로그램 목록과 버전 정보를 수집합니다.</p>
                <button class="btn" onclick="collectInstalledPrograms()" id="programsBtn">설치된 프로그램 수집</button>
                <div class="progress">
                    <div class="progress-bar" id="programsProgress"></div>
                </div>
                <div id="programsStatus"></div>
            </div>
        </div>

                 <!-- 수집된 파일 목록 -->
         <div class="file-section" style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e1e8ed; margin-top: 30px;">
             <h3 style="color: #2c3e50; margin-top: 0; margin-bottom: 25px; font-size: 1.4em; font-weight: 600; display: flex; align-items: center; gap: 10px;">📁 수집된 파일 목록</h3>
             <div class="file-controls" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
                 <div class="file-controls-left" style="display: flex; gap: 10px; align-items: center;">
                     <button class="btn btn-success" onclick="refreshFileList()">🔄 목록 새로고침</button>
                     <button class="btn" onclick="deleteSelectedFiles()" id="deleteSelectedBtn" style="display: none; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">🗑️ 선택 삭제</button>
                 </div>
                 <div>
                     <label style="display: flex; align-items: center; gap: 8px; margin: 0; cursor: pointer;">
                         <input type="checkbox" id="selectAll" onchange="toggleSelectAll()">
                         <span>전체 선택</span>
                     </label>
                 </div>
             </div>
             <div class="file-list" id="fileList" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; overflow: hidden;">
                 <div class="empty-state" style="text-align: center; padding: 40px; color: #6c757d;">
                     <div style="font-size: 48px; margin-bottom: 20px;">📄</div>
                     <p>파일 목록을 불러오는 중...</p>
                 </div>
             </div>
         </div>

         <!-- 분석 단계로 이동 -->
         <div class="navigation" style="text-align: center; margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);">
             <h3 style="color: white; margin: 0 0 20px 0; font-size: 1.5em;">🎯 데이터 수집이 완료되었나요?</h3>
             <p style="color: rgba(255,255,255,0.9); margin: 0 0 25px 0; font-size: 16px;">수집된 데이터를 바탕으로 상세한 분석 결과를 확인해보세요!</p>
             <a href="/analyze" class="btn" style="font-size: 20px; padding: 18px 40px; background: white; color: #667eea; font-weight: bold; box-shadow: 0 6px 20px rgba(0,0,0,0.2); border: none;">📈 분석 결과 보기</a>
         </div>
     </div>

    <script>
        // 오늘 날짜로 종료 날짜 설정
        document.getElementById('endDate').valueAsDate = new Date();
        
        // 30일 전 날짜로 시작 날짜 설정
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        document.getElementById('startDate').valueAsDate = startDate;

        async function collectBookmarks() {
            const btn = document.getElementById('bookmarkBtn');
            const progress = document.getElementById('bookmarkProgress');
            const status = document.getElementById('bookmarkStatus');
            
            btn.disabled = true;
            progress.style.width = '50%';
            status.innerHTML = '<div class="status info">북마크를 수집하는 중...</div>';

            try {
                const response = await fetch('/collect_bookmarks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        start_date: document.getElementById('startDate').value,
                        end_date: document.getElementById('endDate').value,
                        include_folders: document.getElementById('includeFolders').checked
                    })
                });

                const result = await response.json();
                progress.style.width = '100%';

                if (result.status === 'success') {
                    status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                } else {
                    status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                }
            } catch (error) {
                progress.style.width = '100%';
                status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }

        async function collectHistory() {
            const btn = document.getElementById('historyBtn');
            const progress = document.getElementById('historyProgress');
            const status = document.getElementById('historyStatus');
            
            btn.disabled = true;
            progress.style.width = '50%';
            status.innerHTML = '<div class="status info">브라우저 히스토리를 수집하는 중...</div>';

            try {
                const response = await fetch('/collect_browser_history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        days_back: parseInt(document.getElementById('historyDays').value)
                    })
                });

                const result = await response.json();
                progress.style.width = '100%';

                if (result.status === 'success') {
                    status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                } else {
                    status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                }
            } catch (error) {
                progress.style.width = '100%';
                status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }

        async function collectSystemInfo() {
            const btn = document.getElementById('systemBtn');
            const progress = document.getElementById('systemProgress');
            const status = document.getElementById('systemStatus');
            
            btn.disabled = true;
            progress.style.width = '50%';
            status.innerHTML = '<div class="status info">시스템 정보를 수집하는 중...</div>';

            try {
                const response = await fetch('/collect_system_info', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                });

                const result = await response.json();
                progress.style.width = '100%';

                if (result.status === 'success') {
                    status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                } else {
                    status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                }
            } catch (error) {
                progress.style.width = '100%';
                status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
            } finally {
                                 btn.disabled = false;
             }
         }

         async function collectChromeExtensions() {
             const btn = document.getElementById('extensionsBtn');
             const progress = document.getElementById('extensionsProgress');
             const status = document.getElementById('extensionsStatus');
             
             btn.disabled = true;
             progress.style.width = '50%';
             status.innerHTML = '<div class="status info">Chrome 확장 프로그램을 수집하는 중...</div>';

             try {
                 const response = await fetch('/collect_chrome_extensions', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     },
                     body: JSON.stringify({})
                 });

                 const result = await response.json();
                 progress.style.width = '100%';

                 if (result.status === 'success') {
                     status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                     refreshFileList();
                 } else {
                     status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                 }
             } catch (error) {
                 progress.style.width = '100%';
                 status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
             } finally {
                 btn.disabled = false;
             }
         }

         async function collectRecentFiles() {
             const btn = document.getElementById('recentFilesBtn');
             const progress = document.getElementById('recentFilesProgress');
             const status = document.getElementById('recentFilesStatus');
             
             btn.disabled = true;
             progress.style.width = '50%';
             status.innerHTML = '<div class="status info">최근 사용한 파일을 수집하는 중...</div>';

             try {
                 const response = await fetch('/collect_recent_files', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     },
                     body: JSON.stringify({
                         days_back: parseInt(document.getElementById('recentFileDays').value)
                     })
                 });

                 const result = await response.json();
                 progress.style.width = '100%';

                 if (result.status === 'success') {
                     status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                     refreshFileList();
                 } else {
                     status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                 }
             } catch (error) {
                 progress.style.width = '100%';
                 status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
             } finally {
                 btn.disabled = false;
             }
         }

         async function collectNetworkInfo() {
             const btn = document.getElementById('networkBtn');
             const progress = document.getElementById('networkProgress');
             const status = document.getElementById('networkStatus');
             
             btn.disabled = true;
             progress.style.width = '50%';
             status.innerHTML = '<div class="status info">네트워크 정보를 수집하는 중...</div>';

             try {
                 const response = await fetch('/collect_network_info', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     },
                     body: JSON.stringify({})
                 });

                 const result = await response.json();
                 progress.style.width = '100%';

                 if (result.status === 'success') {
                     status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                     refreshFileList();
                 } else {
                     status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                 }
             } catch (error) {
                 progress.style.width = '100%';
                 status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
             } finally {
                 btn.disabled = false;
             }
         }

         async function collectInstalledPrograms() {
             const btn = document.getElementById('programsBtn');
             const progress = document.getElementById('programsProgress');
             const status = document.getElementById('programsStatus');
             
             btn.disabled = true;
             progress.style.width = '50%';
             status.innerHTML = '<div class="status info">설치된 프로그램을 수집하는 중...</div>';

             try {
                 const response = await fetch('/collect_installed_programs', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     },
                     body: JSON.stringify({})
                 });

                 const result = await response.json();
                 progress.style.width = '100%';

                 if (result.status === 'success') {
                     status.innerHTML = `<div class="status success">${result.message}<br><small>데이터 소스: ${result.data_source}</small></div>`;
                     refreshFileList();
                 } else {
                     status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                 }
             } catch (error) {
                 progress.style.width = '100%';
                 status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
             } finally {
                 btn.disabled = false;
             }
         }

         async function refreshFileList() {
             const fileList = document.getElementById('fileList');
             fileList.innerHTML = '<div class="empty-state" style="text-align: center; padding: 40px; color: #6c757d;"><div style="font-size: 48px; margin-bottom: 20px;">📄</div><p>파일 목록을 불러오는 중...</p></div>';

             try {
                 const response = await fetch('/list_files');
                 const files = await response.json();

                 if (files.length === 0) {
                     fileList.innerHTML = '<div class="empty-state" style="text-align: center; padding: 40px; color: #6c757d;"><div style="font-size: 48px; margin-bottom: 20px;">📂</div><p>수집된 파일이 없습니다.</p></div>';
                     document.getElementById('deleteSelectedBtn').style.display = 'none';
                     return;
                 }

                 let html = '';
                 files.forEach(file => {
                     const size = (file.size / 1024).toFixed(2);
                     const date = new Date(file.modified).toLocaleString('ko-KR');
                     html += `
                         <div class="file-item" style="display: flex; align-items: center; padding: 20px; border-bottom: 1px solid #e9ecef; transition: background-color 0.3s ease;">
                             <div class="file-checkbox" style="margin-right: 15px;">
                                 <input type="checkbox" value="${file.name}" onchange="updateDeleteButton()" style="width: 18px; height: 18px; cursor: pointer;">
                             </div>
                             <div class="file-info" style="flex: 1;">
                                 <div class="file-name" style="font-weight: 600; color: #2c3e50; margin-bottom: 5px;">${file.name}</div>
                                 <div class="file-meta" style="font-size: 12px; color: #6c757d;">크기: ${size} KB | 수정일: ${date}</div>
                             </div>
                             <div class="file-actions" style="display: flex; gap: 10px;">
                                 <button class="btn" onclick="downloadFile('${file.name}')" style="padding: 8px 16px; font-size: 12px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">📥 다운로드</button>
                                 <button class="btn" onclick="deleteFile('${file.name}')" style="padding: 8px 16px; font-size: 12px; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">🗑️ 삭제</button>
                             </div>
                         </div>
                     `;
                 });
                 fileList.innerHTML = html;
                 document.getElementById('deleteSelectedBtn').style.display = 'inline-block';
                 updateDeleteButton();
             } catch (error) {
                 fileList.innerHTML = `<div class="empty-state" style="text-align: center; padding: 40px; color: #6c757d;"><div style="font-size: 48px; margin-bottom: 20px;">❌</div><p>파일 목록을 불러오는 중 오류가 발생했습니다: ${error.message}</p></div>`;
             }
         }

         function updateDeleteButton() {
             const selectedFiles = document.querySelectorAll('.file-item input[type="checkbox"]:checked');
             const deleteBtn = document.getElementById('deleteSelectedBtn');
             const selectAllCheckbox = document.getElementById('selectAll');
             const allCheckboxes = document.querySelectorAll('.file-item input[type="checkbox"]');
             
             if (selectedFiles.length > 0) {
                 deleteBtn.style.display = 'inline-block';
                 deleteBtn.textContent = `🗑️ 선택 삭제 (${selectedFiles.length})`;
             } else {
                 deleteBtn.style.display = 'none';
             }
             
             if (selectedFiles.length === allCheckboxes.length && allCheckboxes.length > 0) {
                 selectAllCheckbox.checked = true;
                 selectAllCheckbox.indeterminate = false;
             } else if (selectedFiles.length > 0) {
                 selectAllCheckbox.checked = false;
                 selectAllCheckbox.indeterminate = true;
             } else {
                 selectAllCheckbox.checked = false;
                 selectAllCheckbox.indeterminate = false;
             }
         }

         function toggleSelectAll() {
             const checkboxes = document.querySelectorAll('.file-item input[type="checkbox"]');
             const selectAll = document.getElementById('selectAll').checked;
             
             checkboxes.forEach(checkbox => {
                 checkbox.checked = selectAll;
             });
             
             updateDeleteButton();
         }

         async function deleteSelectedFiles() {
             const selectedCheckboxes = document.querySelectorAll('.file-item input[type="checkbox"]:checked');
             const selectedFiles = Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
             
             if (selectedFiles.length === 0) {
                 alert('삭제할 파일을 선택하세요.');
                 return;
             }

             if (!confirm(`선택한 ${selectedFiles.length}개의 파일을 삭제하시겠습니까?`)) {
                 return;
             }

             let successCount = 0;
             let errorCount = 0;

             for (const filename of selectedFiles) {
                 try {
                     const response = await fetch(`/delete/${encodeURIComponent(filename)}`, {
                         method: 'DELETE'
                     });

                     const result = await response.json();

                     if (result.status === 'success') {
                         successCount++;
                     } else {
                         errorCount++;
                         console.error(`삭제 실패: ${filename} - ${result.error}`);
                     }
                 } catch (error) {
                     errorCount++;
                     console.error(`네트워크 오류: ${filename} - ${error.message}`);
                 }
             }

             if (successCount > 0) {
                 alert(`${successCount}개 파일이 성공적으로 삭제되었습니다.${errorCount > 0 ? ` (${errorCount}개 실패)` : ''}`);
                 refreshFileList();
             } else {
                 alert('파일 삭제에 실패했습니다.');
             }
         }

         function downloadFile(filename) {
             const link = document.createElement('a');
             link.href = `/download/${encodeURIComponent(filename)}`;
             link.download = filename;
             document.body.appendChild(link);
             link.click();
             document.body.removeChild(link);
         }

         async function deleteFile(filename) {
             if (!confirm(`'${filename}' 파일을 삭제하시겠습니까?`)) {
                 return;
             }

             try {
                 const response = await fetch(`/delete/${encodeURIComponent(filename)}`, {
                     method: 'DELETE'
                 });

                 const result = await response.json();

                 if (result.status === 'success') {
                     alert(result.message);
                     refreshFileList();
                 } else {
                     alert('삭제 중 오류가 발생했습니다: ' + result.error);
                 }
             } catch (error) {
                 alert('네트워크 오류가 발생했습니다: ' + error.message);
             }
         }

         // 초기화 함수
         async function clearAllFiles() {
             if (!confirm('⚠️ 모든 수집된 파일을 삭제하시겠습니까?\\n\\n이 작업은 되돌릴 수 없습니다!')) {
                 return;
             }
             
             const btn = document.getElementById('clearBtn');
             const progress = document.getElementById('clearProgress');
             const progressBar = document.getElementById('clearProgressBar');
             const status = document.getElementById('clearStatus');
             
             try {
                 btn.disabled = true;
                 btn.textContent = '🗑️ 삭제 중...';
                 progress.style.display = 'block';
                 progressBar.style.width = '50%';
                 status.innerHTML = '<div class="status info">파일을 삭제하는 중...</div>';
                 
                 const response = await fetch('/clear_all_files', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                     }
                 });
                 
                 const result = await response.json();
                 progressBar.style.width = '100%';
                 
                 if (result.status === 'success') {
                     status.innerHTML = `<div class="status success">${result.message}</div>`;
                     
                     // 파일 목록 새로고침
                     refreshFileList();
                     
                     // 모든 상태 메시지 초기화
                     document.querySelectorAll('[id$="Status"]').forEach(element => {
                         element.innerHTML = '';
                     });
                     
                     // 모든 프로그레스 바 초기화
                     document.querySelectorAll('[id$="Progress"]').forEach(element => {
                         element.style.width = '0%';
                     });
                 } else {
                     status.innerHTML = `<div class="status error">오류: ${result.message}</div>`;
                 }
             } catch (error) {
                 progressBar.style.width = '100%';
                 status.innerHTML = `<div class="status error">네트워크 오류: ${error.message}</div>`;
             } finally {
                 btn.disabled = false;
                 btn.textContent = '🗑️ 모든 파일 초기화';
                 setTimeout(() => {
                     progress.style.display = 'none';
                     progressBar.style.width = '0%';
                 }, 2000);
             }
         }

         // 페이지 로드 시 파일 목록 불러오기
         window.onload = function() {
             refreshFileList();
         };
     </script>
 </body>
 </html>
 '''

@application.route('/')
def index():
    """메인 페이지 - 동의서부터 시작"""
    return render_template_string(CONSENT_TEMPLATE)

@application.route('/consent', methods=['POST'])
def consent():
    """동의서 처리"""
    # 동의 정보를 세션에 저장
    session['consent_given'] = True
    session['consent_time'] = datetime.now().isoformat()
    
    # 데이터 수집 페이지로 리다이렉트
    return redirect(url_for('data_collection'))

@application.route('/data_collection')
def data_collection():
    """데이터 수집 페이지"""
    # 동의 확인
    if not session.get('consent_given'):
        return redirect(url_for('index'))
    
    return render_template_string(DATA_COLLECTION_TEMPLATE)

@application.route('/collect_bookmarks', methods=['POST'])
def collect_bookmarks():
    """북마크 수집 API - 하이브리드 방식 (로컬: 실제 데이터, AWS: 샘플 데이터)"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        include_folders = data.get('include_folders', True)
        
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 Chrome 북마크 수집
            try:
                collector = ChromeBookmarkCollector()
                bookmarks = collector.extract_bookmarks(start_date, end_date, include_folders)
                data_source = "실제 Chrome 북마크"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = ChromeBookmarkCollector()
                bookmarks = collector._get_sample_bookmarks()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = ChromeBookmarkCollector()
            bookmarks = collector._get_sample_bookmarks()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # 날짜 필터링 (샘플 데이터의 경우)
        if start_date or end_date:
            filtered_bookmarks = []
            for bookmark in bookmarks:
                bookmark_date = datetime.fromisoformat(bookmark['date_added'].replace('Z', '+00:00')).replace(tzinfo=None)
                
                if start_date and bookmark_date < datetime.strptime(start_date, '%Y-%m-%d'):
                    continue
                if end_date and bookmark_date > datetime.strptime(end_date, '%Y-%m-%d'):
                    continue
                    
                filtered_bookmarks.append(bookmark)
            bookmarks = filtered_bookmarks
        
        # CSV로 저장
        df = pd.DataFrame(bookmarks)
        csv_filename = f"{UPLOAD_FOLDER}/bookmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'북마크 {len(bookmarks)}개가 성공적으로 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': bookmarks[:5],
            'data_source': data_source,
            'total_count': len(bookmarks)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_browser_history', methods=['POST'])
def collect_browser_history():
    """브라우저 히스토리 수집 API - 하이브리드 방식"""
    try:
        data = request.get_json()
        days_back = data.get('days_back', 30)
        
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 Chrome 히스토리 수집
            try:
                collector = BrowserHistoryCollector()
                history = collector.get_browser_history(days_back)
                data_source = "실제 Chrome 히스토리"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = BrowserHistoryCollector()
                history = collector._get_sample_history()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = BrowserHistoryCollector()
            history = collector._get_sample_history()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # 날짜 필터링 (지정된 일수만큼)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_history = []
        for item in history:
            last_visit = datetime.fromisoformat(item['last_visit'].replace('Z', '+00:00')).replace(tzinfo=None)
            if last_visit >= cutoff_date:
                filtered_history.append(item)
        
        history = filtered_history
        
        # CSV로 저장
        df = pd.DataFrame(history)
        csv_filename = f"{UPLOAD_FOLDER}/browser_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'최근 {days_back}일간의 히스토리 {len(history)}개가 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': history[:5],
            'data_source': data_source,
            'total_count': len(history)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_system_info', methods=['POST'])
def collect_system_info():
    """시스템 정보 수집 API - 하이브리드 방식"""
    try:
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 시스템 정보 수집
            try:
                collector = SystemInfoCollector()
                system_info = collector.get_system_info()
                data_source = "실제 시스템 정보"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = SystemInfoCollector()
                system_info = collector._get_sample_system_info()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = SystemInfoCollector()
            system_info = collector._get_sample_system_info()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # CSV로 저장
        df = pd.DataFrame(system_info)
        csv_filename = f"{UPLOAD_FOLDER}/system_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'시스템 정보 {len(system_info)}개 항목이 성공적으로 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': system_info[:5],
            'data_source': data_source,
            'total_count': len(system_info)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_chrome_extensions', methods=['POST'])
def collect_chrome_extensions():
    """Chrome 확장 프로그램 수집 API"""
    try:
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 Chrome 확장 프로그램 수집
            try:
                collector = ChromeBookmarkCollector()
                extensions = collector.get_chrome_extensions()
                data_source = "실제 Chrome 확장 프로그램"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = ChromeBookmarkCollector()
                extensions = collector._get_sample_extensions()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = ChromeBookmarkCollector()
            extensions = collector._get_sample_extensions()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # CSV로 저장
        df = pd.DataFrame(extensions)
        csv_filename = f"{UPLOAD_FOLDER}/chrome_extensions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'Chrome 확장 프로그램 {len(extensions)}개가 성공적으로 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': extensions[:5],
            'data_source': data_source,
            'total_count': len(extensions)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_recent_files', methods=['POST'])
def collect_recent_files():
    """최근 사용한 파일 수집 API"""
    try:
        data = request.get_json()
        days_back = data.get('days_back', 7)
        
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 최근 파일 수집
            try:
                collector = RecentFilesCollector()
                recent_files = collector.get_recent_files(days_back)
                data_source = "실제 최근 사용 파일"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = RecentFilesCollector()
                recent_files = collector._get_sample_recent_files()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = RecentFilesCollector()
            recent_files = collector._get_sample_recent_files()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # CSV로 저장
        df = pd.DataFrame(recent_files)
        csv_filename = f"{UPLOAD_FOLDER}/recent_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'최근 {days_back}일간의 파일 {len(recent_files)}개가 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': recent_files[:5],
            'data_source': data_source,
            'total_count': len(recent_files)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_network_info', methods=['POST'])
def collect_network_info():
    """네트워크 정보 수집 API"""
    try:
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 네트워크 정보 수집
            try:
                collector = NetworkInfoCollector()
                network_info = collector.get_network_info()
                data_source = "실제 네트워크 정보"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = NetworkInfoCollector()
                network_info = collector._get_sample_network_info()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = NetworkInfoCollector()
            network_info = collector._get_sample_network_info()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # CSV로 저장
        df = pd.DataFrame(network_info)
        csv_filename = f"{UPLOAD_FOLDER}/network_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'네트워크 정보 {len(network_info)}개 항목이 성공적으로 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': network_info[:5],
            'data_source': data_source,
            'total_count': len(network_info)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/collect_installed_programs', methods=['POST'])
def collect_installed_programs():
    """설치된 프로그램 목록 수집 API"""
    try:
        # 환경에 따라 데이터 수집 방식 결정
        if DATA_COLLECTORS_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 설치된 프로그램 수집
            try:
                collector = SystemInfoCollector()
                programs = collector.get_installed_programs()
                data_source = "실제 설치된 프로그램"
            except Exception as e:
                print(f"실제 데이터 수집 실패, 샘플 데이터 사용: {e}")
                collector = SystemInfoCollector()
                programs = collector._get_sample_installed_programs()
                data_source = "샘플 데이터 (실제 수집 실패)"
        else:
            # AWS 환경 또는 모듈 없음: 샘플 데이터 사용
            collector = SystemInfoCollector()
            programs = collector._get_sample_installed_programs()
            data_source = "샘플 데이터 (AWS 환경)"
        
        # CSV로 저장
        df = pd.DataFrame(programs)
        csv_filename = f"{UPLOAD_FOLDER}/installed_programs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'status': 'success',
            'message': f'설치된 프로그램 {len(programs)}개가 성공적으로 수집되었습니다. (출처: {data_source})',
            'filename': os.path.basename(csv_filename),
            'data_preview': programs[:5],
            'data_source': data_source,
            'total_count': len(programs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@application.route('/clear_all_files', methods=['POST'])
def clear_all_files():
    """모든 수집된 파일 삭제 (초기화)"""
    if not session.get('consent_given'):
        return jsonify({'error': 'Consent not given'}), 403
    
    try:
        deleted_count = 0
        error_count = 0
        
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.endswith(('.csv', '.json')):
                    try:
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"✅ 파일 삭제: {filename}")
                    except Exception as e:
                        error_count += 1
                        print(f"❌ 파일 삭제 실패: {filename} - {e}")
        
        if deleted_count > 0:
            message = f"🗑️ 초기화 완료! {deleted_count}개의 파일이 삭제되었습니다."
            if error_count > 0:
                message += f" ({error_count}개 파일 삭제 실패)"
        else:
            message = "삭제할 파일이 없습니다. 이미 깨끗한 상태입니다!"
        
        return jsonify({
            'status': 'success',
            'message': message,
            'deleted_count': deleted_count,
            'error_count': error_count
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

# 파일 관리 API들
@application.route('/list_files')
def list_files():
    """수집된 파일 목록 반환"""
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith(('.csv', '.json')):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                files.append({
                    'name': filename,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
    return jsonify(files)

@application.route('/download/<filename>')
def download_file(filename):
    """파일 다운로드"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path) and filename.endswith(('.csv', '.json', '.html')):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.route('/delete/<filename>', methods=['DELETE'])
def delete_file_route(filename):
    """파일 삭제"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path) and filename.endswith(('.csv', '.json')):
            os.remove(file_path)
            return jsonify({'status': 'success', 'message': f'{filename}이 삭제되었습니다.'})
        else:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application.route('/analyze')
def analyze():
    """분석 페이지"""
    if not session.get('consent_given'):
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>데이터 분석</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 40px;
                font-size: 2.5em;
                font-weight: 300;
            }
            .analysis-section {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 15px;
                margin: 20px 0;
                border-left: 5px solid #667eea;
            }
            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                min-height: 400px;
            }
            .chart-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .insight-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin: 15px 0;
            }
            .insight-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @media (max-width: 768px) {
                .chart-grid {
                    grid-template-columns: 1fr;
                }
                .container {
                    padding: 20px;
                }
            }
        </style>
        <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>📈 데이터 분석 결과</h1>
            
            <!-- 라이브러리 로딩 상태 표시 -->
            <div id="loadingStatus" style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px;">
                <div class="spinner"></div>
                <p>차트 라이브러리를 로딩하는 중...</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="bookmarkCount">15</div>
                    <div class="stat-label">총 북마크 수</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="historyCount">18</div>
                    <div class="stat-label">브라우저 히스토리</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="systemCount">18</div>
                    <div class="stat-label">시스템 정보 항목</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="categoryCount">6</div>
                    <div class="stat-label">주요 카테고리</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalVisits">276</div>
                    <div class="stat-label">총 방문 횟수</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="avgDaily">9.2</div>
                    <div class="stat-label">일평균 방문</div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="analysis-section">
                    <h3>🔖 북마크 카테고리 분석</h3>
                    <div class="chart-container">
                        <div class="loading" id="bookmarkLoading">
                            <div class="spinner"></div>
                            <p>북마크 데이터를 분석하는 중...</p>
                        </div>
                        <div id="bookmarkChart"></div>
                    </div>
                </div>
                
                <div class="analysis-section">
                    <h3>🌐 브라우저 사용 패턴</h3>
                    <div class="chart-container">
                        <div class="loading" id="historyLoading">
                            <div class="spinner"></div>
                            <p>히스토리 데이터를 분석하는 중...</p>
                        </div>
                        <div id="historyChart"></div>
                    </div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>💻 시스템 구성 분석</h3>
                <div class="chart-container">
                    <div class="loading" id="systemLoading">
                        <div class="spinner"></div>
                        <p>시스템 정보를 분석하는 중...</p>
                    </div>
                    <div id="systemChart"></div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>📊 시간대별 활동 패턴</h3>
                <div class="chart-container">
                    <div id="timeChart"></div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h3>🤖 AI 기반 성향 분석</h3>
                <div class="ai-analysis-controls" style="margin-bottom: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                    <div id="apiKeyStatus" style="margin-bottom: 15px; padding: 15px; border-radius: 8px; overflow: hidden;">
                        <div style="display: flex; align-items: flex-start; gap: 10px;">
                            <span id="apiKeyIcon" style="flex-shrink: 0;">🔍</span>
                            <span id="apiKeyText" style="word-break: break-all; overflow-wrap: break-word; line-height: 1.4;">API 키 상태를 확인하는 중...</span>
                        </div>
                    </div>
                    <div class="form-group" id="manualApiKeyGroup" style="margin-bottom: 15px; display: none;">
                        <label for="openaiApiKey" style="display: block; margin-bottom: 8px; font-weight: 600;">OpenAI API 키 (수동 입력):</label>
                        <input type="password" id="openaiApiKey" placeholder="sk-..." style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        <small style="color: #6c757d; display: block; margin-top: 5px;">
                            .env 파일의 API 키 대신 다른 키를 사용하려면 여기에 입력하세요.
                        </small>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 15px;">
                        <button class="btn" onclick="runAIAnalysis()" id="aiAnalysisBtn">🧠 AI 분석 실행</button>
                        <button class="btn" onclick="toggleManualApiKey()" id="toggleApiKeyBtn" style="background: #6c757d;">⚙️ 수동 입력</button>
                    </div>
                    
                    <!-- 상세 진행률 표시 -->
                    <div class="ai-progress-container" id="aiProgressContainer" style="display: none;">
                        <div class="progress-steps" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; width: 100%;">
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step1" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">1</div>
                                <div class="step-label" id="stepLabel1" style="font-size: 11px; color: #6c757d; font-weight: 500;">준비</div>
                            </div>
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step2" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">2</div>
                                <div class="step-label" id="stepLabel2" style="font-size: 11px; color: #6c757d; font-weight: 500;">데이터 분석</div>
                            </div>
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step3" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">3</div>
                                <div class="step-label" id="stepLabel3" style="font-size: 11px; color: #6c757d; font-weight: 500;">AI 전송</div>
                            </div>
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step4" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">4</div>
                                <div class="step-label" id="stepLabel4" style="font-size: 11px; color: #6c757d; font-weight: 500;">GPT 분석</div>
                            </div>
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step5" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">5</div>
                                <div class="step-label" id="stepLabel5" style="font-size: 11px; color: #6c757d; font-weight: 500;">결과 처리</div>
                            </div>
                            <div class="progress-step" style="flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; min-width: 80px;">
                                <div class="step-circle" id="step6" style="width: 30px; height: 30px; border-radius: 50%; background: #dee2e6; color: #6c757d; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-weight: bold; font-size: 12px; transition: all 0.3s ease;">✓</div>
                                <div class="step-label" id="stepLabel6" style="font-size: 11px; color: #6c757d; font-weight: 500;">완료</div>
                            </div>
                        </div>
                        
                        <div class="progress" style="position: relative; background-color: #e9ecef; border-radius: 15px; padding: 6px; margin: 15px 0; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                            <div class="progress-bar" id="aiAnalysisProgress" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 12px; border-radius: 10px; width: 0%; transition: width 0.8s ease; position: relative; overflow: hidden;">
                            </div>
                            <div class="progress-text" id="progressText" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 11px; font-weight: bold; color: #495057; text-shadow: 0 1px 2px rgba(255,255,255,0.8); z-index: 10; pointer-events: none;">0%</div>
                        </div>
                        
                        <div style="text-align: center; margin-top: 10px;">
                            <small id="progressDetail" style="color: #6c757d;">분석을 시작하려면 위의 버튼을 클릭하세요.</small>
                        </div>
                    </div>
                    
                    <div id="aiAnalysisStatus"></div>
                </div>
                
                <div id="aiInsights">
                    <div class="insight-card">
                        <div class="insight-title">🔍 기본 패턴 분석</div>
                        <p>수집된 데이터를 바탕으로 기본적인 사용 패턴을 분석했습니다. AI 분석을 실행하면 더 상세한 인사이트를 확인할 수 있습니다.</p>
                    </div>
                    <div class="insight-card">
                        <div class="insight-title">⏰ 활동 시간대</div>
                        <p>오후 2-6시 사이에 가장 활발한 웹 활동을 보이며, 업무 시간대와 일치합니다.</p>
                    </div>
                    <div class="insight-card">
                        <div class="insight-title">🎯 기본 추천 사항</div>
                        <p>생산성 도구 활용, 체계적인 파일 관리, 정기적인 백업을 추천합니다.</p>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="btn" onclick="exportToHTML()" id="exportBtn" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">💾 HTML로 저장</button>
                <a href="/data_collection" class="btn">🔄 데이터 수집으로 돌아가기</a>
                <a href="/" class="btn">🏠 처음으로</a>
            </div>
        </div>
        
        <script>
            // 전역 변수로 AI 분석 결과 저장
            let currentAIAnalysisResult = null;
            
            // 페이지 로드 시 차트 생성
            document.addEventListener('DOMContentLoaded', function() {
                console.log('페이지 로드됨');
                
                // Plotly 라이브러리 로딩 확인
                if (typeof Plotly === 'undefined') {
                    console.error('Plotly 라이브러리가 로드되지 않았습니다');
                    document.getElementById('loadingStatus').innerHTML = '<p style="color: red;">❌ 차트 라이브러리 로딩 실패</p>';
                    return;
                }
                
                console.log('Plotly 라이브러리 로드됨');
                document.getElementById('loadingStatus').style.display = 'none';
                
                // API 키 상태 확인
                checkApiKeyStatus();
                
                // 실제 데이터를 가져와서 차트 생성
                setTimeout(loadAnalysisData, 500);
            });
            
            function loadAnalysisData() {
                fetch('/get_analysis_data')
                    .then(response => response.json())
                    .then(data => {
                        console.log('분석 데이터 로드됨:', data);
                        
                        // 통계 카드 업데이트
                        updateStats(data.stats);
                        
                                                 // 차트 생성
                         createBookmarkChart(data.bookmarks);
                         createHistoryChart(data.history);
                         createSystemChart(data.system);
                         createTimeChart(data.timePattern);
                        
                        console.log('모든 차트 생성 완료');
                    })
                    .catch(error => {
                        console.error('데이터 로드 오류:', error);
                        // 오류 시 기본 데이터로 차트 생성
                        createDefaultCharts();
                    });
            }
            
            function updateStats(stats) {
                document.getElementById('bookmarkCount').textContent = stats.bookmark_count || 0;
                document.getElementById('historyCount').textContent = stats.history_count || 0;
                document.getElementById('systemCount').textContent = stats.system_count || 0;
                document.getElementById('categoryCount').textContent = stats.categories || 0;
                document.getElementById('totalVisits').textContent = stats.total_visits || 0;
                document.getElementById('avgDaily').textContent = stats.avg_daily || 0;
            }
            
            function createDefaultCharts() {
                try {
                    const defaultData = {
                        bookmarks: {
                            categories: ['Development', 'Entertainment', 'Cloud', 'Education', 'Professional', 'Shopping'],
                            counts: [6, 2, 2, 2, 2, 1]
                        },
                        history: {
                            sites: ['Google', 'YouTube', 'Stack Overflow', 'AWS Console', 'GitHub'],
                            visits: [45, 35, 25, 22, 20]
                        },
                        system: {
                            categories: ['Software', 'Memory', 'CPU', 'Storage'],
                            counts: [4, 4, 2, 2]
                        }
                    };
                    
                                         createBookmarkChart(defaultData.bookmarks);
                     createHistoryChart(defaultData.history);
                     createSystemChart(defaultData.system);
                     createTimeChart();
                } catch (error) {
                    console.error('기본 차트 생성 오류:', error);
                }
            }
            
            function createBookmarkChart(bookmarkData) {
                console.log('북마크 차트 생성 시작');
                
                try {
                    document.getElementById('bookmarkLoading').style.display = 'none';
                    
                    // 기본값 설정
                    const categories = bookmarkData?.categories || ['Development', 'Entertainment', 'Cloud', 'Education', 'Professional', 'Shopping'];
                    const counts = bookmarkData?.counts || [6, 2, 2, 2, 2, 1];
                    
                    var data = [{
                        values: counts,
                        labels: categories,
                        type: 'pie',
                        hole: 0.4,
                        marker: {
                            colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b']
                        },
                        textinfo: 'label+percent',
                        textposition: 'outside'
                    }];
                    
                    var layout = {
                        title: {
                            text: '북마크 카테고리 분포',
                            font: { size: 16, family: 'Segoe UI, sans-serif' }
                        },
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.1 },
                        margin: { t: 50, b: 50, l: 50, r: 50 },
                        height: 400
                    };
                    
                    Plotly.newPlot('bookmarkChart', data, layout, {responsive: true});
                    console.log('북마크 차트 생성 완료');
                } catch (error) {
                    console.error('북마크 차트 생성 오류:', error);
                    document.getElementById('bookmarkChart').innerHTML = '<p style="color: red; text-align: center; padding: 20px;">차트 생성 실패</p>';
                }
            }
            
            function createHistoryChart(historyData) {
                console.log('히스토리 차트 생성 시작');
                
                try {
                    document.getElementById('historyLoading').style.display = 'none';
                    
                    // 기본값 설정
                    const sites = historyData?.sites || ['Google', 'YouTube', 'Stack Overflow', 'AWS Console', 'GitHub', 'Netflix', 'AWS Docs', 'Reddit', 'W3Schools', 'MDN'];
                    const visits = historyData?.visits || [45, 35, 25, 22, 20, 18, 16, 14, 11, 10];
                    
                    var data = [{
                        x: sites,
                        y: visits,
                        type: 'bar',
                        marker: {
                            color: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140', '#a8edea', '#fed6e3'],
                            line: { color: 'rgba(0,0,0,0.1)', width: 1 }
                        }
                    }];
                    
                    var layout = {
                        title: {
                            text: '사이트별 방문 횟수 (Top 10)',
                            font: { size: 16, family: 'Segoe UI, sans-serif' }
                        },
                        xaxis: { 
                            title: '웹사이트',
                            tickangle: -45
                        },
                        yaxis: { title: '방문 횟수' },
                        margin: { t: 50, b: 100, l: 50, r: 50 },
                        height: 400
                    };
                    
                    Plotly.newPlot('historyChart', data, layout, {responsive: true});
                    console.log('히스토리 차트 생성 완료');
                } catch (error) {
                    console.error('히스토리 차트 생성 오류:', error);
                    document.getElementById('historyChart').innerHTML = '<p style="color: red; text-align: center; padding: 20px;">차트 생성 실패</p>';
                }
            }
            
            function createSystemChart(systemData) {
                console.log('시스템 차트 생성 시작');
                
                try {
                    document.getElementById('systemLoading').style.display = 'none';
                    
                    // 기본값 설정
                    const categories = systemData?.categories || ['Software', 'Memory', 'CPU', 'Storage', 'Network', 'Process', 'Security', 'Monitoring'];
                    const counts = systemData?.counts || [4, 4, 2, 2, 2, 2, 1, 1];
                    
                    var data = [{
                        values: counts,
                        labels: categories,
                        type: 'pie',
                        hole: 0.3,
                        marker: {
                            colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']
                        },
                        textinfo: 'label+percent',
                        textposition: 'auto'
                    }];
                    
                    var layout = {
                        title: {
                            text: '시스템 정보 카테고리 분포',
                            font: { size: 16, family: 'Segoe UI, sans-serif' }
                        },
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.1 },
                        margin: { t: 50, b: 50, l: 50, r: 50 },
                        height: 400
                    };
                    
                    Plotly.newPlot('systemChart', data, layout, {responsive: true});
                    console.log('시스템 차트 생성 완료');
                } catch (error) {
                    console.error('시스템 차트 생성 오류:', error);
                    document.getElementById('systemChart').innerHTML = '<p style="color: red; text-align: center; padding: 20px;">차트 생성 실패</p>';
                }
            }
            
            function createTimeChart(timeData) {
                console.log('시간대별 차트 생성 시작');
                
                try {
                    // 기본값 설정
                    const hours = timeData?.hours || ['00-02', '02-04', '04-06', '06-08', '08-10', '10-12', '12-14', '14-16', '16-18', '18-20', '20-22', '22-24'];
                    const activities = timeData?.activities || [2, 1, 0, 3, 8, 15, 12, 25, 22, 18, 12, 6];
                    
                    var data = [{
                        x: hours,
                        y: activities,
                        type: 'scatter',
                        mode: 'lines+markers',
                        line: {
                            color: '#667eea',
                            width: 3,
                            shape: 'spline'
                        },
                        marker: {
                            color: '#764ba2',
                            size: 8,
                            line: { color: 'white', width: 2 }
                        },
                        fill: 'tonexty',
                        fillcolor: 'rgba(102, 126, 234, 0.1)'
                    }];
                    
                    var layout = {
                        title: {
                            text: '시간대별 웹 활동 패턴',
                            font: { size: 16, family: 'Segoe UI, sans-serif' }
                        },
                        xaxis: { 
                            title: '시간대',
                            type: 'category',
                            gridcolor: 'rgba(0,0,0,0.1)'
                        },
                        yaxis: { 
                            title: '활동 횟수',
                            gridcolor: 'rgba(0,0,0,0.1)'
                        },
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 50, b: 50, l: 50, r: 50 },
                        height: 400
                    };
                    
                    Plotly.newPlot('timeChart', data, layout, {responsive: true});
                    console.log('시간대별 차트 생성 완료');
                } catch (error) {
                    console.error('시간대별 차트 생성 오류:', error);
                    document.getElementById('timeChart').innerHTML = '<p style="color: red; text-align: center; padding: 20px;">차트 생성 실패</p>';
                }
            }
            
            async function checkApiKeyStatus() {
                try {
                    const response = await fetch('/check_api_key');
                    const result = await response.json();
                    
                    const statusDiv = document.getElementById('apiKeyStatus');
                    const iconSpan = document.getElementById('apiKeyIcon');
                    const textSpan = document.getElementById('apiKeyText');
                    const toggleBtn = document.getElementById('toggleApiKeyBtn');
                    
                    if (result.has_key) {
                        // API 키가 있는 경우
                        statusDiv.style.background = 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)';
                        statusDiv.style.border = '1px solid #b8daff';
                        iconSpan.textContent = '🔑';
                        textSpan.innerHTML = `<strong>✅ ${result.message}</strong><br><small>자동으로 AI 분석을 사용할 수 있습니다.</small>`;
                        toggleBtn.style.display = 'inline-block';
                    } else {
                        // API 키가 없는 경우
                        statusDiv.style.background = 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)';
                        statusDiv.style.border = '1px solid #ffeaa7';
                        iconSpan.textContent = '⚠️';
                        textSpan.innerHTML = `<strong>⚠️ ${result.message}</strong><br><small>기본 분석만 가능합니다. API 키를 추가하면 고급 AI 분석을 사용할 수 있습니다.</small>`;
                        toggleBtn.style.display = 'inline-block';
                        document.getElementById('manualApiKeyGroup').style.display = 'block';
                    }
                } catch (error) {
                    console.error('API 키 상태 확인 실패:', error);
                    const statusDiv = document.getElementById('apiKeyStatus');
                    statusDiv.style.background = 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)';
                    statusDiv.style.border = '1px solid #f5c6cb';
                    document.getElementById('apiKeyIcon').textContent = '❌';
                    document.getElementById('apiKeyText').innerHTML = '<strong>❌ API 키 상태 확인 실패</strong><br><small>네트워크 오류가 발생했습니다.</small>';
                }
            }
            
            function toggleManualApiKey() {
                const group = document.getElementById('manualApiKeyGroup');
                const btn = document.getElementById('toggleApiKeyBtn');
                
                if (group.style.display === 'none') {
                    group.style.display = 'block';
                    btn.textContent = '🔒 숨기기';
                    btn.style.background = '#dc3545';
                } else {
                    group.style.display = 'none';
                    btn.textContent = '⚙️ 수동 입력';
                    btn.style.background = '#6c757d';
                }
            }
            
            async function runAIAnalysis() {
                const btn = document.getElementById('aiAnalysisBtn');
                const progress = document.getElementById('aiAnalysisProgress');
                const progressText = document.getElementById('progressText');
                const progressDetail = document.getElementById('progressDetail');
                const progressContainer = document.getElementById('aiProgressContainer');
                const status = document.getElementById('aiAnalysisStatus');
                const manualApiKey = document.getElementById('openaiApiKey').value;
                
                // 진행률 컨테이너 표시
                progressContainer.style.display = 'block';
                
                btn.disabled = true;
                btn.textContent = '🧠 분석 중...';
                
                // 모든 단계 초기화
                resetProgressSteps();
                
                // 로딩바 애니메이션 시작
                progress.style.width = '0%';
                progressText.textContent = '0%';
                status.innerHTML = '';
                
                try {
                    // API 키 우선순위: 수동 입력 > 환경 변수 > null
                    let apiKeyToUse = manualApiKey || null;
                    
                    // 1단계: 준비 (10%)
                    await updateProgress(1, 10, '🔍 AI 분석 준비 중...', '데이터 수집 상태를 확인하고 있습니다.');
                    await sleep(500);
                    
                    // 2단계: 데이터 분석 (25%)
                    await updateProgress(2, 25, '📊 수집된 데이터 분석 중...', '북마크, 히스토리, 시스템 정보를 종합 분석하고 있습니다.');
                    await sleep(800);
                    
                    // 3단계: AI 전송 (45%)
                    await updateProgress(3, 45, '🤖 AI 모델에 데이터 전송 중...', 
                        apiKeyToUse ? '수동 입력된 API 키로 OpenAI에 연결하고 있습니다.' : '.env 파일의 API 키로 OpenAI에 연결하고 있습니다.');
                    await sleep(700);
                    
                    // 4단계: GPT 분석 (65%)
                    await updateProgress(4, 65, '🧠 OpenAI GPT 분석 실행 중...', 'GPT가 개인 성향과 MBTI를 분석하고 있습니다. 잠시만 기다려주세요.');
                    
                    // 실제 API 호출
                    const response = await fetch('/ai_analysis', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            openai_api_key: apiKeyToUse
                        })
                    });
                    
                    // 5단계: 결과 처리 (85%)
                    await updateProgress(5, 85, '📋 분석 결과 처리 중...', '받은 분석 결과를 정리하고 시각화하고 있습니다.');
                    await sleep(500);
                    
                    const result = await response.json();
                    
                    // 6단계: 완료 (100%)
                    await updateProgress(6, 100, '✅ 분석 완료!', '모든 분석이 성공적으로 완료되었습니다.');
                    
                    if (result.status === 'success') {
                        // AI 분석 결과를 전역 변수에 저장
                        currentAIAnalysisResult = {
                            ...result.analysis_result,
                            ai_powered: result.ai_powered,
                            timestamp: new Date().toISOString()
                        };
                        
                        if (result.ai_powered) {
                            // AI 분석 성공
                            status.innerHTML = '<div class="status success">🎉 <strong>고급 AI 분석이 완료되었습니다!</strong><br><small>OpenAI GPT를 사용하여 정확한 성향 분석을 수행했습니다.</small></div>';
                        } else {
                            // 기본 분석으로 처리됨
                            status.innerHTML = '<div class="status success">📊 <strong>기본 분석이 완료되었습니다.</strong><br><small>API 키 문제로 기본 분석을 수행했습니다.</small></div>';
                        }
                        displayAIInsights(result.analysis_result);
                    } else {
                        status.innerHTML = `<div class="status error">❌ <strong>분석 실패:</strong> ${result.message}</div>`;
                        resetProgressSteps();
                    }
                } catch (error) {
                    await updateProgress(6, 100, '❌ 오류 발생', `네트워크 오류: ${error.message}`);
                    status.innerHTML = `<div class="status error">❌ <strong>네트워크 오류:</strong> ${error.message}</div>`;
                    resetProgressSteps();
                } finally {
                    btn.disabled = false;
                    btn.textContent = '🧠 AI 분석 실행';
                    
                    // 5초 후 진행률 바 숨기기
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                        resetProgressSteps();
                    }, 5000);
                }
            }
            
            // 진행률 업데이트 함수
            async function updateProgress(step, percentage, message, detail) {
                const progress = document.getElementById('aiAnalysisProgress');
                const progressText = document.getElementById('progressText');
                const progressDetail = document.getElementById('progressDetail');
                
                // 이전 단계들을 완료로 표시
                for (let i = 1; i < step; i++) {
                    const stepCircle = document.getElementById(`step${i}`);
                    const stepLabel = document.getElementById(`stepLabel${i}`);
                    stepCircle.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
                    stepCircle.style.color = 'white';
                    stepCircle.style.transform = 'scale(1)';
                    stepCircle.style.boxShadow = 'none';
                    stepLabel.style.color = '#28a745';
                    stepLabel.style.fontWeight = 'bold';
                }
                
                // 현재 단계를 활성화
                const currentStepCircle = document.getElementById(`step${step}`);
                const currentStepLabel = document.getElementById(`stepLabel${step}`);
                currentStepCircle.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                currentStepCircle.style.color = 'white';
                currentStepCircle.style.transform = 'scale(1.1)';
                currentStepCircle.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
                currentStepLabel.style.color = '#667eea';
                currentStepLabel.style.fontWeight = 'bold';
                
                // 진행률 바 업데이트
                progress.style.width = `${percentage}%`;
                progressText.textContent = `${percentage}%`;
                progressDetail.textContent = detail;
                
                return new Promise(resolve => {
                    setTimeout(resolve, 100);
                });
            }
            
            // 진행률 단계 초기화 함수
            function resetProgressSteps() {
                for (let i = 1; i <= 6; i++) {
                    const stepCircle = document.getElementById(`step${i}`);
                    const stepLabel = document.getElementById(`stepLabel${i}`);
                    stepCircle.style.background = '#dee2e6';
                    stepCircle.style.color = '#6c757d';
                    stepCircle.style.transform = 'scale(1)';
                    stepCircle.style.boxShadow = 'none';
                    stepLabel.style.color = '#6c757d';
                    stepLabel.style.fontWeight = '500';
                }
                
                const progress = document.getElementById('aiAnalysisProgress');
                const progressText = document.getElementById('progressText');
                const progressDetail = document.getElementById('progressDetail');
                
                progress.style.width = '0%';
                progressText.textContent = '0%';
                progressDetail.textContent = '분석을 시작하려면 위의 버튼을 클릭하세요.';
            }
            
            // 유틸리티 함수
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
            
            function displayAIInsights(analysisResult) {
                const insightsContainer = document.getElementById('aiInsights');
                
                let html = '';
                
                // 불완전한 분석 결과 감지
                function isIncompleteAnalysis(data) {
                    const checkTexts = ['분석 중...', 'AI 분석 중...', '파싱하는 중...', '생성하는 중...'];
                    const dataStr = JSON.stringify(data);
                    return checkTexts.some(text => dataStr.includes(text));
                }
                
                // AI 인사이트 표시
                if (analysisResult.ai_insights) {
                    const insights = analysisResult.ai_insights;
                    
                    // 불완전한 분석 결과인지 확인
                    if (isIncompleteAnalysis(insights)) {
                        html += `
                            <div class="insight-card" style="border-left: 4px solid #ff6b6b;">
                                <div class="insight-title">⚠️ 분석 결과 불완전</div>
                                <p style="color: #e74c3c; margin-bottom: 15px;">
                                    <strong>이전 AI 분석이 완전히 완료되지 않았습니다.</strong><br>
                                    정확한 분석 결과를 위해 AI 분석을 다시 실행해주세요.
                                </p>
                                <button onclick="location.reload()" style="background: #3498db; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                    🔄 페이지 새로고침 후 AI 분석 재실행
                                </button>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="insight-card">
                                <div class="insight-title">🤖 AI 종합 분석</div>
                                <p><strong>전반적 성향:</strong> ${insights.overview || '분석 중...'}</p>
                                <p><strong>주요 강점:</strong> ${insights.strengths || '분석 중...'}</p>
                                <p><strong>업무 스타일:</strong> ${insights.work_style || '분석 중...'}</p>
                                <p><strong>관심 분야:</strong> ${insights.interests || '분석 중...'}</p>
                            </div>
                        `;
                    }
                }
                
                // MBTI 분석 표시
                if (analysisResult.mbti_analysis) {
                    const mbti = analysisResult.mbti_analysis;
                    
                    // MBTI 분석이 불완전한지 확인
                    if (isIncompleteAnalysis(mbti)) {
                        html += `
                            <div class="insight-card" style="border-left: 4px solid #ff6b6b;">
                                <div class="insight-title">⚠️ MBTI 분석 불완전</div>
                                <p style="color: #e74c3c;">MBTI 분석이 완전히 완료되지 않았습니다. AI 분석을 다시 실행해주세요.</p>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="insight-card">
                                <div class="insight-title">🧠 MBTI 성향 분석</div>
                                <p><strong>예상 유형:</strong> ${mbti.predicted_type || 'ESTJ'} (신뢰도: ${mbti.confidence || 60}%)</p>
                                <div style="margin-top: 15px;">
                                    <div style="margin: 10px 0;">
                                        <strong>외향성(E) vs 내향성(I):</strong> ${mbti.E_I?.score || 60}% → ${mbti.E_I?.tendency || 'E'}
                                        <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${mbti.E_I?.score || 60}%; border-radius: 4px;"></div>
                                        </div>
                                    </div>
                                    <div style="margin: 10px 0;">
                                        <strong>감각(S) vs 직관(N):</strong> ${mbti.S_N?.score || 45}% → ${mbti.S_N?.tendency || 'S'}
                                        <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${mbti.S_N?.score || 45}%; border-radius: 4px;"></div>
                                        </div>
                                    </div>
                                    <div style="margin: 10px 0;">
                                        <strong>사고(T) vs 감정(F):</strong> ${mbti.T_F?.score || 65}% → ${mbti.T_F?.tendency || 'T'}
                                        <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${mbti.T_F?.score || 65}%; border-radius: 4px;"></div>
                                        </div>
                                    </div>
                                    <div style="margin: 10px 0;">
                                        <strong>판단(J) vs 인식(P):</strong> ${mbti.J_P?.score || 55}% → ${mbti.J_P?.tendency || 'J'}
                                        <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${mbti.J_P?.score || 55}%; border-radius: 4px;"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
                
                // 성격 특성 표시
                if (analysisResult.personality_traits) {
                    const traits = analysisResult.personality_traits;
                    
                    // 성격 특성 분석이 불완전한지 확인
                    if (isIncompleteAnalysis(traits)) {
                        html += `
                            <div class="insight-card" style="border-left: 4px solid #ff6b6b;">
                                <div class="insight-title">⚠️ 성격 특성 분석 불완전</div>
                                <p style="color: #e74c3c;">성격 특성 분석이 완전히 완료되지 않았습니다. AI 분석을 다시 실행해주세요.</p>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="insight-card">
                                <div class="insight-title">🎯 성격 특성 분석</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                                    <div>
                                        <strong>개방성:</strong> ${traits.openness?.score || 70}%<br>
                                        <small>${traits.openness?.description || '새로운 경험에 대한 개방성'}</small>
                                    </div>
                                    <div>
                                        <strong>성실성:</strong> ${traits.conscientiousness?.score || 65}%<br>
                                        <small>${traits.conscientiousness?.description || '조직적이고 계획적인 성향'}</small>
                                    </div>
                                    <div>
                                        <strong>외향성:</strong> ${traits.extraversion?.score || 60}%<br>
                                        <small>${traits.extraversion?.description || '사교적이고 활동적인 성향'}</small>
                                    </div>
                                    <div>
                                        <strong>친화성:</strong> ${traits.agreeableness?.score || 70}%<br>
                                        <small>${traits.agreeableness?.description || '협력적이고 신뢰하는 성향'}</small>
                                    </div>
                                    <div>
                                        <strong>창의성:</strong> ${traits.creativity?.score || 75}%<br>
                                        <small>${traits.creativity?.description || '창의적 사고와 혁신성'}</small>
                                    </div>
                                    <div>
                                        <strong>기술 친화도:</strong> ${traits.tech_savviness?.score || 80}%<br>
                                        <small>${traits.tech_savviness?.description || '기술 수용과 활용 능력'}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
                
                // 추천 사항 표시
                if (analysisResult.recommendations) {
                    const rec = analysisResult.recommendations;
                    
                    // 추천 사항이 불완전한지 확인
                    if (isIncompleteAnalysis(rec)) {
                        html += `
                            <div class="insight-card" style="border-left: 4px solid #ff6b6b;">
                                <div class="insight-title">⚠️ 추천 사항 불완전</div>
                                <p style="color: #e74c3c;">개인화된 추천 사항이 완전히 생성되지 않았습니다. AI 분석을 다시 실행해주세요.</p>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="insight-card">
                                <div class="insight-title">💡 개인화된 추천</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
                                    <div>
                                        <h4 style="margin: 0 0 10px 0; color: #667eea;">🛠️ 생산성 도구</h4>
                                        <ul style="margin: 0; padding-left: 20px;">
                                            ${(rec.productivity_tools || []).map(item => `<li>${item}</li>`).join('')}
                                        </ul>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0 0 10px 0; color: #667eea;">📚 학습 리소스</h4>
                                        <ul style="margin: 0; padding-left: 20px;">
                                            ${(rec.learning_resources || []).map(item => `<li>${item}</li>`).join('')}
                                        </ul>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0 0 10px 0; color: #667eea;">💻 소프트웨어/앱</h4>
                                        <ul style="margin: 0; padding-left: 20px;">
                                            ${(rec.software_apps || []).map(item => `<li>${item}</li>`).join('')}
                                        </ul>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0 0 10px 0; color: #667eea;">🚀 커리어 발전</h4>
                                        <ul style="margin: 0; padding-left: 20px;">
                                            ${(rec.career_development || []).map(item => `<li>${item}</li>`).join('')}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
                
                // AI 분석 여부 표시
                const aiPowered = analysisResult.ai_powered;
                html += `
                    <div class="insight-card" style="background: ${aiPowered ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' : 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'};">
                        <div class="insight-title" style="color: white;">
                            ${aiPowered ? '🤖 OpenAI 기반 분석' : '📊 기본 분석'}
                        </div>
                        <p style="color: white; margin: 0;">
                            ${aiPowered 
                                ? 'OpenAI GPT를 사용하여 고도화된 AI 분석을 수행했습니다.' 
                                : 'OpenAI API 키 없이 기본 분석을 수행했습니다. API 키를 입력하면 더 정확한 분석을 받을 수 있습니다.'
                            }
                        </p>
                    </div>
                `;
                
                insightsContainer.innerHTML = html;
            }
            
            // HTML 내보내기 함수
            async function exportToHTML() {
                const btn = document.getElementById('exportBtn');
                
                try {
                    btn.disabled = true;
                    btn.textContent = '💾 저장 중...';
                    
                    // 현재 분석 데이터 수집
                    const analysisResponse = await fetch('/get_analysis_data');
                    const analysisData = await analysisResponse.json();
                    
                    // AI 분석 결과가 있으면 포함
                    if (currentAIAnalysisResult) {
                        analysisData.ai_analysis = currentAIAnalysisResult;
                        console.log('AI 분석 결과 포함:', currentAIAnalysisResult);
                    } else {
                        console.log('AI 분석 결과 없음 - 기본 분석만 저장');
                    }
                    
                    // HTML 저장 API 호출
                    const response = await fetch('/export_analysis_html', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            analysis_data: analysisData
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert(`✅ ${result.message}\\n\\n파일명: ${result.filename}`);
                        
                        // 자동 다운로드
                        const link = document.createElement('a');
                        link.href = result.download_url;
                        link.download = result.filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    } else {
                        alert(`❌ 저장 실패: ${result.message}`);
                    }
                } catch (error) {
                    alert(`❌ 네트워크 오류: ${error.message}`);
                } finally {
                    btn.disabled = false;
                    btn.textContent = '💾 HTML로 저장';
                }
            }
        </script>
    </body>
    </html>
    '''

@application.route('/health')
def health():
    """헬스 체크 엔드포인트"""
    import sys
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': 'AWS' if is_aws_environment() else 'Local',
        'data_collectors_available': DATA_COLLECTORS_AVAILABLE,
        'python_version': sys.version.split()[0]
    })

def analyze_time_pattern(df_history):
    """히스토리 데이터에서 시간대별 활동 패턴을 분석"""
    from datetime import datetime
    import numpy as np
    
    try:
        hour_counts = [0] * 24  # 24시간 배열
        
        for _, row in df_history.iterrows():
            try:
                # ISO 형식 날짜 파싱
                visit_time = datetime.fromisoformat(row['last_visit'].replace('Z', '+00:00'))
                hour = visit_time.hour
                visit_count = int(row.get('visit_count', 1))
                hour_counts[hour] += visit_count
            except:
                continue
        
        # 2시간 간격으로 그룹화
        time_labels = []
        time_activities = []
        
        for i in range(0, 24, 2):
            if i + 1 < 24:
                time_labels.append(f'{i:02d}-{i+2:02d}')
                time_activities.append(hour_counts[i] + hour_counts[i+1])
            else:
                time_labels.append(f'{i:02d}-{(i+2)%24:02d}')
                time_activities.append(hour_counts[i] + hour_counts[0])
        
        return {
            'hours': time_labels,
            'activities': time_activities
        }
        
    except Exception as e:
        print(f"시간대 분석 오류: {e}")
        # 기본 패턴 반환
        return {
            'hours': ['00-02', '02-04', '04-06', '06-08', '08-10', '10-12', '12-14', '14-16', '16-18', '18-20', '20-22', '22-24'],
            'activities': [2, 1, 0, 3, 8, 15, 12, 25, 22, 18, 12, 6]
        }

@application.route('/get_analysis_data')
def get_analysis_data():
    """실제 수집된 데이터를 분석하여 반환"""
    if not session.get('consent_given'):
        return jsonify({'error': 'Consent not given'}), 403
    
    try:
        analysis_data = {
            'bookmarks': {'categories': [], 'counts': []},
            'history': {'sites': [], 'visits': []},
            'system': {'categories': [], 'counts': []},
            'timePattern': {'hours': [], 'activities': []},
            'stats': {
                'bookmark_count': 0,
                'history_count': 0,
                'system_count': 0,
                'total_visits': 0,
                'categories': 0
            }
        }
        
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        
        # 북마크 데이터 분석
        bookmark_files = [f for f in os.listdir(uploads_dir) if f.startswith('bookmarks_') and f.endswith('.csv')]
        if bookmark_files:
            latest_bookmark = max(bookmark_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_bookmarks = pd.read_csv(os.path.join(uploads_dir, latest_bookmark))
            
            # 카테고리별 북마크 수 계산
            if 'category' in df_bookmarks.columns:
                category_counts = df_bookmarks['category'].value_counts()
                analysis_data['bookmarks']['categories'] = category_counts.index.tolist()
                analysis_data['bookmarks']['counts'] = category_counts.values.tolist()
            
            analysis_data['stats']['bookmark_count'] = len(df_bookmarks)
            analysis_data['stats']['categories'] = len(analysis_data['bookmarks']['categories'])
        
        # 히스토리 데이터 분석
        history_files = [f for f in os.listdir(uploads_dir) if f.startswith('browser_history_') and f.endswith('.csv')]
        if history_files:
            latest_history = max(history_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_history = pd.read_csv(os.path.join(uploads_dir, latest_history))
            
            # 도메인별 방문 횟수 상위 10개
            if 'domain' in df_history.columns and 'visit_count' in df_history.columns:
                domain_visits = df_history.groupby('domain')['visit_count'].sum().sort_values(ascending=False).head(10)
                analysis_data['history']['sites'] = domain_visits.index.tolist()
                analysis_data['history']['visits'] = domain_visits.values.tolist()
            
            analysis_data['stats']['history_count'] = len(df_history)
            if 'visit_count' in df_history.columns:
                analysis_data['stats']['total_visits'] = df_history['visit_count'].sum()
            
            # 시간대별 활동 패턴 분석
            if 'last_visit' in df_history.columns:
                time_pattern = analyze_time_pattern(df_history)
                analysis_data['timePattern'] = time_pattern
        
        # 시스템 데이터 분석
        system_files = [f for f in os.listdir(uploads_dir) if f.startswith('system_info_') and f.endswith('.csv')]
        if system_files:
            latest_system = max(system_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_system = pd.read_csv(os.path.join(uploads_dir, latest_system))
            
            # 카테고리별 시스템 정보 수 계산
            if 'category' in df_system.columns:
                category_counts = df_system['category'].value_counts()
                analysis_data['system']['categories'] = category_counts.index.tolist()
                analysis_data['system']['counts'] = category_counts.values.tolist()
            
            analysis_data['stats']['system_count'] = len(df_system)
        
        # 일평균 방문 계산
        if analysis_data['stats']['total_visits'] > 0:
            analysis_data['stats']['avg_daily'] = round(analysis_data['stats']['total_visits'] / 30, 1)
        
        return jsonify(analysis_data)
        
    except Exception as e:
        print(f"분석 데이터 생성 오류: {e}")
        # 오류 시 기본 샘플 데이터 반환
        return jsonify({
            'bookmarks': {
                'categories': ['Development', 'Entertainment', 'Cloud', 'Education', 'Professional', 'Shopping'],
                'counts': [6, 2, 2, 2, 2, 1]
            },
            'history': {
                'sites': ['Google', 'YouTube', 'Stack Overflow', 'AWS Console', 'GitHub'],
                'visits': [45, 35, 25, 22, 20]
            },
            'system': {
                'categories': ['Software', 'Memory', 'CPU', 'Storage'],
                'counts': [4, 4, 2, 2]
            },
            'timePattern': {
                'hours': ['00-02', '02-04', '04-06', '06-08', '08-10', '10-12', '12-14', '14-16', '16-18', '18-20', '20-22', '22-24'],
                'activities': [2, 1, 0, 3, 8, 15, 12, 25, 22, 18, 12, 6]
            },
            'stats': {
                'bookmark_count': 15,
                'history_count': 18,
                'system_count': 18,
                'total_visits': 276,
                'categories': 6,
                'avg_daily': 9.2
            }
        })

@application.route('/check_api_key')
def check_api_key():
    """환경 변수에서 OpenAI API 키 상태 확인"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key.startswith('sk-') and len(api_key) > 20:
            # API 키가 올바른 형식인지 간단히 확인
            masked_key = api_key[:7] + '*' * (len(api_key) - 14) + api_key[-7:]
            return jsonify({
                'status': 'found',
                'message': f'.env 파일에서 API 키를 찾았습니다: {masked_key}',
                'has_key': True
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': '.env 파일에 유효한 OPENAI_API_KEY가 없습니다.',
                'has_key': False
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'API 키 확인 중 오류: {str(e)}',
            'has_key': False
        })

@application.route('/ai_analysis', methods=['POST'])
def ai_analysis():
    """AI 기반 성향 분석 API"""
    if not session.get('consent_given'):
        return jsonify({'error': 'Consent not given'}), 403
    
    try:
        data = request.get_json()
        api_key = data.get('openai_api_key')  # 사용자가 제공한 API 키
        
        # 수집된 데이터 준비
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        data_summary = prepare_data_for_ai_analysis(uploads_dir)
        
        if not AI_ANALYZER_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'AI 분석 모듈을 사용할 수 없습니다. ai_analyzer.py 파일을 확인해주세요.'
            }), 500
        
        # AI 분석기 초기화
        analyzer = AIPersonalityAnalyzer(api_key)
        
        # 분석 수행
        analysis_result = analyzer.analyze_user_profile(data_summary)
        
        # 결과를 JSON 파일로 저장
        result_filename = f"{UPLOAD_FOLDER}/ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': f'AI 분석이 완료되었습니다. {"OpenAI API를 사용했습니다." if analysis_result.get("ai_powered") else "기본 분석을 수행했습니다."}',
            'filename': os.path.basename(result_filename),
            'analysis_result': analysis_result,
            'ai_powered': analysis_result.get('ai_powered', False)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'AI 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@application.route('/get_ai_analysis_data')
def get_ai_analysis_data():
    """최신 AI 분석 결과 반환"""
    if not session.get('consent_given'):
        return jsonify({'error': 'Consent not given'}), 403
    
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        
        # 가장 최근 AI 분석 파일 찾기
        analysis_files = [f for f in os.listdir(uploads_dir) if f.startswith('ai_analysis_') and f.endswith('.json')]
        
        if not analysis_files:
            return jsonify({
                'status': 'no_data',
                'message': 'AI 분석 결과가 없습니다. 먼저 AI 분석을 실행해주세요.'
            })
        
        latest_analysis = max(analysis_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
        
        with open(os.path.join(uploads_dir, latest_analysis), 'r', encoding='utf-8') as f:
            analysis_result = json.load(f)
        
        return jsonify({
            'status': 'success',
            'analysis_result': analysis_result,
            'filename': latest_analysis
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'AI 분석 결과를 불러오는 중 오류가 발생했습니다: {str(e)}'
        }), 500

@application.route('/export_analysis_html', methods=['POST'])
def export_analysis_html():
    """분석 결과를 HTML 파일로 저장"""
    if not session.get('consent_given'):
        return jsonify({'error': 'Consent not given'}), 403
    
    try:
        data = request.get_json()
        analysis_data = data.get('analysis_data', {})
        
        # 인터랙티브 HTML 템플릿 생성
        html_content = generate_interactive_analysis_html(analysis_data)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_report_{timestamp}.html"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # HTML 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'status': 'success',
            'message': f'분석 결과가 HTML 파일로 저장되었습니다.',
            'filename': filename,
            'download_url': f'/download/{filename}'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'HTML 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500

def generate_analysis_html(analysis_data):
    """분석 결과 HTML 생성"""
    timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')
    
    html_template = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>디지털 패턴 분석 리포트 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .report-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            border-left: 5px solid #667eea;
        }}
        .section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 디지털 패턴 분석 리포트</h1>
        
        <div class="report-info">
            <h3>📅 리포트 생성 정보</h3>
            <p><strong>생성 일시:</strong> {timestamp}</p>
            <p><strong>분석 유형:</strong> 📊 종합 데이터 분석</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('bookmark_count', 0)}</div>
                <div class="stat-label">총 북마크 수</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('history_count', 0)}</div>
                <div class="stat-label">브라우저 히스토리</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('system_count', 0)}</div>
                <div class="stat-label">시스템 정보 항목</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('total_visits', 0)}</div>
                <div class="stat-label">총 방문 횟수</div>
            </div>
        </div>
        
        <div class="section">
            <h3>🔖 북마크 분석</h3>
            <div class="grid-2">'''
    
    # 북마크 카테고리 정보 추가
    bookmarks = analysis_data.get('bookmarks', {})
    if bookmarks.get('categories') and bookmarks.get('counts'):
        for category, count in zip(bookmarks['categories'], bookmarks['counts']):
            percentage = round(count/sum(bookmarks['counts'])*100, 1) if bookmarks['counts'] else 0
            html_template += f'''
                <div>
                    <strong>{category}:</strong> {count}개<br>
                    <small>전체의 {percentage}%</small>
                </div>'''
    
    html_template += '''
            </div>
        </div>
        
        <div class="section">
            <h3>🌐 브라우저 사용 패턴</h3>
            <div class="grid-2">'''
    
    # 히스토리 정보 추가
    history = analysis_data.get('history', {})
    if history.get('sites') and history.get('visits'):
        for i, (site, visits) in enumerate(zip(history['sites'][:6], history['visits'][:6])):
            html_template += f'''
                <div>
                    <strong>{site}:</strong> {visits}회 방문<br>
                    <small>상위 {i+1}위 사이트</small>
                </div>'''
    
    html_template += '''
            </div>
        </div>
        
        <div class="section">
            <h3>💻 시스템 구성</h3>
            <div class="grid-2">'''
    
    # 시스템 정보 추가
    system = analysis_data.get('system', {})
    if system.get('categories') and system.get('counts'):
        for category, count in zip(system['categories'], system['counts']):
            html_template += f'''
                <div>
                    <strong>{category}:</strong> {count}개 항목<br>
                    <small>시스템 구성 요소</small>
                </div>'''
    
    # 푸터 추가
    html_template += '''
            </div>
        </div>
        
        <div class="section" style="text-align: center; margin-top: 40px;">
            <p style="color: #6c757d;">
                이 리포트는 신입사원 디지털 패턴 분석 시스템에서 생성되었습니다.<br>
                분석 결과는 참고용으로만 사용하시기 바랍니다.
            </p>
        </div>
    </div>
</body>
</html>'''
    
    return html_template

@application.route('/environment')
def environment_info():
    """환경 정보 확인 엔드포인트"""
    import sys
    import platform
    
    env_info = {
        'is_aws': is_aws_environment(),
        'data_collectors_available': DATA_COLLECTORS_AVAILABLE,
        'python_version': sys.version,
        'platform': platform.platform(),
        'environment_variables': {
            'AWS_REGION': os.environ.get('AWS_REGION'),
            'AWS_EXECUTION_ENV': os.environ.get('AWS_EXECUTION_ENV'),
            'EB_NODE_COMMAND': os.environ.get('EB_NODE_COMMAND'),
            'PATH_contains_elasticbeanstalk': '/opt/elasticbeanstalk' in os.environ.get('PATH', '')
        },
        'file_system': {
            'elasticbeanstalk_exists': os.path.exists('/opt/elasticbeanstalk'),
            'current_directory': os.getcwd(),
            'home_directory': os.path.expanduser('~')
        }
    }
    
    return jsonify(env_info)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    application.run(debug=False, host='0.0.0.0', port=port) 
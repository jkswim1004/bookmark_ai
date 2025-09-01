"""
AI 기반 사용자 성향 분석 모듈
OpenAI GPT를 사용하여 수집된 데이터로부터 심층적인 인사이트 생성
"""
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경 변수 로드
    print("✅ .env 파일 로드 성공")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv로 설치하세요.")

# OpenAI API 설정
try:
    import openai
    OPENAI_AVAILABLE = True
    print("✅ OpenAI 라이브러리 로드 성공")
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. pip install openai로 설치하세요.")

def convert_numpy_types(obj):
    """numpy 타입을 JSON 직렬화 가능한 Python 기본 타입으로 변환"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

class AIPersonalityAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """AI 성향 분석기 초기화"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                # OpenAI v1.0+ 방식으로 클라이언트 초기화
                self.client = openai.OpenAI(api_key=self.api_key)
                self.ai_enabled = True
                print(f"✅ OpenAI API 연결 성공 (키: {self.api_key[:7]}...{self.api_key[-7:]})")
            except Exception as e:
                print(f"❌ OpenAI API 초기화 실패: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
            print(f"⚠️ OpenAI API 키가 없습니다. 기본 분석 모드로 작동합니다. (키: {self.api_key})")
    
    def analyze_user_profile(self, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """수집된 데이터를 종합하여 사용자 프로필 분석"""
        print(f"🔍 AI 분석 시작 - AI 활성화 상태: {self.ai_enabled}")
        print(f"🔑 API 키 존재: {bool(self.api_key)}")
        
        if not self.ai_enabled:
            print("⚠️ AI가 비활성화되어 기본 분석을 수행합니다.")
            return self._get_basic_analysis(data_summary)
        
        try:
            print("🚀 AI 기반 분석을 시작합니다...")
            
            # AI 분석 수행
            print("📊 AI 인사이트 생성 중...")
            ai_insights = self._generate_ai_insights(data_summary)
            
            print("🧠 MBTI 분석 중...")
            mbti_analysis = self._analyze_mbti(data_summary)
            
            print("🎯 성격 특성 분석 중...")
            personality_traits = self._analyze_personality_traits(data_summary)
            
            print("💡 추천 생성 중...")
            recommendations = self._generate_recommendations(data_summary)
            
            print("✅ AI 분석 완료!")
            return {
                'ai_insights': ai_insights,
                'mbti_analysis': mbti_analysis,
                'personality_traits': personality_traits,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now().isoformat(),
                'ai_powered': True
            }
        except Exception as e:
            print(f"❌ AI 분석 실패, 기본 분석으로 전환: {e}")
            import traceback
            traceback.print_exc()
            return self._get_basic_analysis(data_summary)
    
    def _generate_ai_insights(self, data_summary: Dict[str, Any]) -> Dict[str, str]:
        """AI를 사용하여 종합적인 인사이트 생성"""
        prompt = self._create_analysis_prompt(data_summary)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 디지털 행동 패턴 분석 전문가입니다. 
                        사용자의 브라우저 사용 패턴, 설치된 프로그램, 파일 사용 현황을 바탕으로 
                        성격, 업무 스타일, 관심사를 분석해주세요. 
                        한국어로 친근하고 이해하기 쉽게 설명해주세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # 응답을 구조화된 형태로 파싱
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            print(f"AI 인사이트 생성 실패: {e}")
            return {
                'overview': '데이터 분석 중 오류가 발생했습니다.',
                'strengths': '분석할 수 없음',
                'work_style': '분석할 수 없음',
                'interests': '분석할 수 없음'
            }
    
    def _analyze_mbti(self, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """MBTI 성향 분석"""
        if not self.ai_enabled:
            return self._get_basic_mbti()
        
        mbti_prompt = f"""
        다음 사용자 데이터를 바탕으로 MBTI 성향을 분석해주세요:
        
        브라우저 사용 패턴: {data_summary.get('browser_patterns', {})}
        설치된 프로그램: {data_summary.get('software_categories', {})}
        파일 사용 패턴: {data_summary.get('file_patterns', {})}
        네트워크 활동: {data_summary.get('network_activity', {})}
        
        각 MBTI 차원에 대해 0-100 점수로 평가하고 근거를 제시해주세요:
        - E(외향성) vs I(내향성)
        - S(감각) vs N(직관)  
        - T(사고) vs F(감정)
        - J(판단) vs P(인식)
        
        JSON 형식으로 응답해주세요.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 MBTI 전문가입니다. 디지털 사용 패턴을 바탕으로 정확한 MBTI 분석을 제공해주세요."
                    },
                    {
                        "role": "user",
                        "content": mbti_prompt
                    }
                ],
                max_tokens=800,
                temperature=0.5
            )
            
            mbti_response = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                return json.loads(mbti_response)
            except:
                return self._parse_mbti_text(mbti_response)
                
        except Exception as e:
            print(f"MBTI 분석 실패: {e}")
            return self._get_basic_mbti()
    
    def _analyze_personality_traits(self, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """성격 특성 분석 (Big 5 등)"""
        if not self.ai_enabled:
            return self._get_basic_personality()
        
        # numpy 타입을 JSON 직렬화 가능한 타입으로 변환
        clean_data = convert_numpy_types(data_summary)
        
        traits_prompt = f"""
        다음 데이터를 바탕으로 사용자의 성격 특성을 분석해주세요:
        
        {json.dumps(clean_data, ensure_ascii=False, indent=2)}
        
        다음 특성들을 0-100 점수로 평가해주세요:
        - 개방성 (새로운 경험에 대한 개방성)
        - 성실성 (조직적이고 계획적인 성향)
        - 외향성 (사교적이고 활동적인 성향)
        - 친화성 (협력적이고 신뢰하는 성향)
        - 신경성 (스트레스에 대한 민감성)
        - 창의성 (창의적 사고와 혁신성)
        - 기술 친화도 (기술 수용과 활용 능력)
        
        각 점수에 대한 근거도 함께 제시해주세요.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 심리학 전문가입니다. 디지털 행동 패턴을 통해 성격 특성을 정확히 분석해주세요."
                    },
                    {
                        "role": "user",
                        "content": traits_prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            return self._parse_personality_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"성격 특성 분석 실패: {e}")
            return self._get_basic_personality()
    
    def _generate_recommendations(self, data_summary: Dict[str, Any]) -> Dict[str, List[str]]:
        """개인화된 추천 생성"""
        if not self.ai_enabled:
            return self._get_basic_recommendations()
        
        # numpy 타입을 JSON 직렬화 가능한 타입으로 변환
        clean_data = convert_numpy_types(data_summary)
        
        rec_prompt = f"""
        다음 사용자 프로필을 바탕으로 개인화된 추천을 생성해주세요:
        
        {json.dumps(clean_data, ensure_ascii=False, indent=2)}
        
        다음 카테고리별로 구체적인 추천을 제시해주세요:
        1. 생산성 도구 (업무 효율성 향상)
        2. 학습 리소스 (기술 및 지식 향상)
        3. 소프트웨어/앱 (현재 사용 패턴 기반)
        4. 업무 스타일 개선 (더 나은 작업 환경)
        5. 커리어 발전 (성향에 맞는 방향성)
        
        각 카테고리당 3-5개의 구체적인 추천을 해주세요.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 개인 생산성 및 커리어 컨설턴트입니다. 사용자의 디지털 패턴을 바탕으로 실용적인 추천을 제공해주세요."
                    },
                    {
                        "role": "user",
                        "content": rec_prompt
                    }
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            return self._parse_recommendations_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"추천 생성 실패: {e}")
            return self._get_basic_recommendations()
    
    def _create_analysis_prompt(self, data_summary: Dict[str, Any]) -> str:
        """분석용 프롬프트 생성"""
        return f"""
        사용자의 디지털 사용 패턴을 분석해주세요:
        
        📊 수집된 데이터:
        - 북마크 카테고리: {data_summary.get('bookmark_categories', [])}
        - 브라우저 히스토리: {data_summary.get('top_sites', [])}
        - 설치된 프로그램: {data_summary.get('software_categories', {})}
        - Chrome 확장 프로그램: {data_summary.get('extensions', [])}
        - 최근 사용 파일: {data_summary.get('recent_files', [])}
        - 네트워크 활동: {data_summary.get('network_stats', {})}
        
        📈 통계:
        - 총 북마크 수: {data_summary.get('total_bookmarks', 0)}
        - 총 방문 사이트: {data_summary.get('total_visits', 0)}
        - 설치된 프로그램 수: {data_summary.get('total_programs', 0)}
        
        이 데이터를 바탕으로 다음을 분석해주세요:
        1. 전반적인 디지털 사용 성향
        2. 주요 강점과 특징
        3. 업무 스타일과 선호도
        4. 관심 분야와 전문성
        """
    
    def _parse_ai_response(self, response: str) -> Dict[str, str]:
        """AI 응답을 구조화된 형태로 파싱"""
        print(f"🔍 AI 응답 파싱 중... (응답 길이: {len(response)})")
        
        # 먼저 JSON 형식인지 확인
        try:
            json_response = json.loads(response)
            if isinstance(json_response, dict):
                return {
                    'overview': json_response.get('overview', json_response.get('전반적_성향', '')),
                    'strengths': json_response.get('strengths', json_response.get('주요_강점', '')),
                    'work_style': json_response.get('work_style', json_response.get('업무_스타일', '')),
                    'interests': json_response.get('interests', json_response.get('관심_분야', ''))
                }
        except:
            pass
        
        # 텍스트 파싱
        lines = response.split('\n')
        
        result = {
            'overview': '',
            'strengths': '',
            'work_style': '',
            'interests': ''
        }
        
        current_section = 'overview'
        content_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 구분자 감지
            if any(keyword in line for keyword in ['강점', 'strength', '장점']):
                current_section = 'strengths'
                continue
            elif any(keyword in line for keyword in ['업무', 'work', '스타일', '작업']):
                current_section = 'work_style'
                continue
            elif any(keyword in line for keyword in ['관심', 'interest', '취미', '분야']):
                current_section = 'interests'
                continue
            elif any(keyword in line for keyword in ['성향', '특징', '분석', '개요']):
                current_section = 'overview'
                continue
            
            # 내용 추가 (불필요한 기호 제거)
            clean_line = line.replace('**', '').replace('##', '').replace('- ', '').strip()
            if clean_line and not clean_line.startswith('#'):
                result[current_section] += clean_line + ' '
                content_found = True
        
        # 파싱된 내용이 없으면 전체 응답을 overview에 저장
        if not content_found:
            result['overview'] = response[:500] + '...' if len(response) > 500 else response
        
        # 빈 섹션에 기본값 설정
        for key, value in result.items():
            if not value.strip():
                result[key] = f"AI 분석 결과를 {key} 항목으로 분류할 수 없었습니다."
        
        print(f"✅ AI 응답 파싱 완료 - 섹션별 길이: {[(k, len(v)) for k, v in result.items()]}")
        return result
    
    def _parse_mbti_text(self, response: str) -> Dict[str, Any]:
        """MBTI 텍스트 응답 파싱"""
        print(f"🧠 MBTI 응답 파싱 중... (응답 길이: {len(response)})")
        
        # 기본값 설정
        result = {
            'E_I': {'score': 60, 'tendency': 'E', 'description': '외향적 성향으로 추정됩니다.'},
            'S_N': {'score': 50, 'tendency': 'S', 'description': '감각적 성향으로 추정됩니다.'},
            'T_F': {'score': 65, 'tendency': 'T', 'description': '논리적 사고 성향으로 추정됩니다.'},
            'J_P': {'score': 55, 'tendency': 'J', 'description': '계획적 성향으로 추정됩니다.'},
            'predicted_type': 'ESTJ',
            'confidence': 70
        }
        
        # 응답에서 점수 추출 시도
        import re
        
        # E/I 점수 찾기
        ei_match = re.search(r'[EI].*?(\d+)', response)
        if ei_match:
            score = int(ei_match.group(1))
            result['E_I']['score'] = score
            result['E_I']['tendency'] = 'E' if score > 50 else 'I'
            result['E_I']['description'] = f"{'외향적' if score > 50 else '내향적'} 성향 {score}%"
        
        # S/N 점수 찾기
        sn_match = re.search(r'[SN].*?(\d+)', response)
        if sn_match:
            score = int(sn_match.group(1))
            result['S_N']['score'] = score
            result['S_N']['tendency'] = 'S' if score > 50 else 'N'
            result['S_N']['description'] = f"{'감각적' if score > 50 else '직관적'} 성향 {score}%"
        
        # T/F 점수 찾기
        tf_match = re.search(r'[TF].*?(\d+)', response)
        if tf_match:
            score = int(tf_match.group(1))
            result['T_F']['score'] = score
            result['T_F']['tendency'] = 'T' if score > 50 else 'F'
            result['T_F']['description'] = f"{'사고형' if score > 50 else '감정형'} 성향 {score}%"
        
        # J/P 점수 �기
        jp_match = re.search(r'[JP].*?(\d+)', response)
        if jp_match:
            score = int(jp_match.group(1))
            result['J_P']['score'] = score
            result['J_P']['tendency'] = 'J' if score > 50 else 'P'
            result['J_P']['description'] = f"{'판단형' if score > 50 else '인식형'} 성향 {score}%"
        
        # MBTI 유형 결정
        mbti_type = (result['E_I']['tendency'] + 
                    result['S_N']['tendency'] + 
                    result['T_F']['tendency'] + 
                    result['J_P']['tendency'])
        result['predicted_type'] = mbti_type
        
        # 신뢰도 계산 (평균 점수 기반)
        scores = [abs(result[key]['score'] - 50) for key in ['E_I', 'S_N', 'T_F', 'J_P']]
        result['confidence'] = min(90, max(60, int(sum(scores) / len(scores) * 2 + 50)))
        
        print(f"✅ MBTI 파싱 완료 - 유형: {mbti_type}, 신뢰도: {result['confidence']}%")
        return result
    
    def _parse_personality_response(self, response: str) -> Dict[str, Any]:
        """성격 특성 응답 파싱"""
        print(f"🎯 성격 특성 응답 파싱 중... (응답 길이: {len(response)})")
        
        # 기본값 설정
        result = {
            'openness': {'score': 75, 'description': '새로운 경험에 개방적인 성향을 보입니다.'},
            'conscientiousness': {'score': 68, 'description': '성실하고 조직적인 성향을 보입니다.'},
            'extraversion': {'score': 62, 'description': '사교적이고 활동적인 성향을 보입니다.'},
            'agreeableness': {'score': 71, 'description': '협력적이고 친화적인 성향을 보입니다.'},
            'neuroticism': {'score': 35, 'description': '정서적으로 안정적인 성향을 보입니다.'},
            'creativity': {'score': 78, 'description': '창의적이고 혁신적인 사고를 보입니다.'},
            'tech_savviness': {'score': 85, 'description': '기술에 능숙하고 적응력이 뛰어납니다.'}
        }
        
        # JSON 파싱 시도
        try:
            json_response = json.loads(response)
            if isinstance(json_response, dict):
                for key in result.keys():
                    if key in json_response:
                        if isinstance(json_response[key], dict):
                            result[key].update(json_response[key])
                        elif isinstance(json_response[key], (int, float)):
                            result[key]['score'] = int(json_response[key])
                return result
        except:
            pass
        
        # 텍스트에서 점수 추출
        import re
        
        # 각 특성별 점수 찾기
        traits_mapping = {
            'openness': ['개방성', 'openness', '개방적'],
            'conscientiousness': ['성실성', 'conscientiousness', '성실'],
            'extraversion': ['외향성', 'extraversion', '외향적'],
            'agreeableness': ['친화성', 'agreeableness', '친화적'],
            'neuroticism': ['신경성', 'neuroticism', '불안'],
            'creativity': ['창의성', 'creativity', '창의적'],
            'tech_savviness': ['기술', 'tech', '테크']
        }
        
        for trait, keywords in traits_mapping.items():
            for keyword in keywords:
                # 키워드 다음에 나오는 숫자 찾기
                pattern = rf'{keyword}.*?(\d+)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    score = int(match.group(1))
                    if 0 <= score <= 100:
                        result[trait]['score'] = score
                        result[trait]['description'] = f"{keyword} 점수: {score}점"
                        break
        
        print(f"✅ 성격 특성 파싱 완료 - 평균 점수: {sum(t['score'] for t in result.values()) / len(result):.1f}")
        return result
    
    def _parse_recommendations_response(self, response: str) -> Dict[str, List[str]]:
        """추천 응답 파싱"""
        print(f"💡 추천 사항 응답 파싱 중... (응답 길이: {len(response)})")
        
        # 기본값 설정
        result = {
            'productivity_tools': ['Notion - 올인원 워크스페이스', 'Todoist - 작업 관리', 'RescueTime - 시간 추적'],
            'learning_resources': ['Coursera - 온라인 강의', 'YouTube - 무료 튜토리얼', 'Stack Overflow - 개발 Q&A'],
            'software_apps': ['VS Code - 코드 에디터', 'Chrome - 웹 브라우저', 'Slack - 팀 커뮤니케이션'],
            'work_style': ['정기적인 휴식 시간 확보', '작업 우선순위 설정', '집중 시간 블록 활용'],
            'career_development': ['기술 블로그 작성', '오픈소스 프로젝트 참여', '네트워킹 이벤트 참석']
        }
        
        # JSON 파싱 시도
        try:
            json_response = json.loads(response)
            if isinstance(json_response, dict):
                for key in result.keys():
                    if key in json_response and isinstance(json_response[key], list):
                        result[key] = json_response[key]
                return result
        except:
            pass
        
        # 텍스트에서 추천 사항 추출
        lines = response.split('\n')
        current_category = None
        
        categories_mapping = {
            'productivity_tools': ['생산성', 'productivity', '도구', 'tool'],
            'learning_resources': ['학습', 'learning', '교육', 'education', '리소스'],
            'software_apps': ['소프트웨어', 'software', '앱', 'app', '프로그램'],
            'work_style': ['업무', 'work', '스타일', 'style', '방식'],
            'career_development': ['커리어', 'career', '발전', 'development', '성장']
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 카테고리 감지
            for category, keywords in categories_mapping.items():
                if any(keyword in line.lower() for keyword in keywords):
                    current_category = category
                    result[category] = []  # 해당 카테고리 초기화
                    break
            
            # 추천 항목 추출 (-, *, 숫자로 시작하는 리스트 항목)
            if current_category and (line.startswith('-') or line.startswith('*') or 
                                   line.startswith('•') or any(line.startswith(f'{i}.') for i in range(1, 10))):
                item = line.lstrip('-*•0123456789. ').strip()
                if item and len(item) > 3:  # 너무 짧은 항목 제외
                    result[current_category].append(item)
        
        # 빈 카테고리에 기본 추천 유지
        for category, items in result.items():
            if not items:
                if category == 'productivity_tools':
                    result[category] = ['Notion', 'Trello', 'Todoist']
                elif category == 'learning_resources':
                    result[category] = ['온라인 강의 플랫폼', '기술 블로그', '전문 서적']
                elif category == 'software_apps':
                    result[category] = ['개발 도구', '디자인 소프트웨어', '커뮤니케이션 앱']
                elif category == 'work_style':
                    result[category] = ['체계적 계획 수립', '정기적 검토', '효율적 시간 관리']
                elif category == 'career_development':
                    result[category] = ['지속적 학습', '네트워킹', '프로젝트 경험 쌓기']
        
        total_recommendations = sum(len(items) for items in result.values())
        print(f"✅ 추천 사항 파싱 완료 - 총 {total_recommendations}개 추천")
        return result
    
    def _get_basic_analysis(self, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """AI 없이 기본 분석 수행"""
        return {
            'ai_insights': {
                'overview': '수집된 데이터를 바탕으로 기본 분석을 수행했습니다.',
                'strengths': '다양한 디지털 도구를 활용하는 능력이 있습니다.',
                'work_style': '체계적이고 효율적인 작업 방식을 선호합니다.',
                'interests': '기술과 생산성에 관심이 많습니다.'
            },
            'mbti_analysis': self._get_basic_mbti(),
            'personality_traits': self._get_basic_personality(),
            'recommendations': self._get_basic_recommendations(),
            'analysis_timestamp': datetime.now().isoformat(),
            'ai_powered': False
        }
    
    def _get_basic_mbti(self) -> Dict[str, Any]:
        """기본 MBTI 분석"""
        return {
            'E_I': {'score': 60, 'tendency': 'E', 'description': '소셜 도구 사용 패턴 기반 분석'},
            'S_N': {'score': 45, 'tendency': 'S', 'description': '실용적 도구 선호 경향'},
            'T_F': {'score': 65, 'tendency': 'T', 'description': '논리적 도구 사용 패턴'},
            'J_P': {'score': 55, 'tendency': 'J', 'description': '체계적 파일 관리 패턴'},
            'predicted_type': 'ESTJ',
            'confidence': 60
        }
    
    def _get_basic_personality(self) -> Dict[str, Any]:
        """기본 성격 특성"""
        return {
            'openness': {'score': 70, 'description': '다양한 도구와 기술 사용'},
            'conscientiousness': {'score': 65, 'description': '체계적인 파일 관리'},
            'extraversion': {'score': 60, 'description': '협업 도구 사용 패턴'},
            'agreeableness': {'score': 70, 'description': '커뮤니케이션 도구 활용'},
            'neuroticism': {'score': 40, 'description': '안정적인 사용 패턴'},
            'creativity': {'score': 75, 'description': '창작 도구 사용'},
            'tech_savviness': {'score': 80, 'description': '고급 기술 도구 활용'}
        }
    
    def _get_basic_recommendations(self) -> Dict[str, List[str]]:
        """기본 추천"""
        return {
            'productivity_tools': [
                'Notion - 통합 워크스페이스',
                'Todoist - 작업 관리',
                'RescueTime - 시간 추적'
            ],
            'learning_resources': [
                'Coursera - 온라인 강의',
                'Udemy - 기술 교육',
                'LinkedIn Learning - 전문 스킬'
            ],
            'software_apps': [
                'VS Code - 코드 에디터',
                'Figma - 디자인 도구',
                'Slack - 팀 커뮤니케이션'
            ],
            'work_style': [
                '포모도로 기법 활용',
                '정기적인 백업 습관',
                '키보드 단축키 학습'
            ],
            'career_development': [
                '기술 블로그 작성',
                '오픈소스 프로젝트 참여',
                '온라인 포트폴리오 구축'
            ]
        }

def prepare_data_for_ai_analysis(uploads_dir: str) -> Dict[str, Any]:
    """수집된 데이터를 AI 분석용으로 준비"""
    data_summary = {
        'bookmark_categories': [],
        'top_sites': [],
        'software_categories': {},
        'extensions': [],
        'recent_files': [],
        'network_stats': {},
        'total_bookmarks': 0,
        'total_visits': 0,
        'total_programs': 0
    }
    
    try:
        # 북마크 데이터 처리
        bookmark_files = [f for f in os.listdir(uploads_dir) if f.startswith('bookmarks_') and f.endswith('.csv')]
        if bookmark_files:
            latest_bookmark = max(bookmark_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_bookmarks = pd.read_csv(os.path.join(uploads_dir, latest_bookmark))
            
            if 'folder' in df_bookmarks.columns:
                data_summary['bookmark_categories'] = df_bookmarks['folder'].value_counts().head(10).to_dict()
            data_summary['total_bookmarks'] = len(df_bookmarks)
        
        # 히스토리 데이터 처리
        history_files = [f for f in os.listdir(uploads_dir) if f.startswith('browser_history_') and f.endswith('.csv')]
        if history_files:
            latest_history = max(history_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_history = pd.read_csv(os.path.join(uploads_dir, latest_history))
            
            if 'domain' in df_history.columns:
                data_summary['top_sites'] = df_history['domain'].value_counts().head(10).to_dict()
            if 'visit_count' in df_history.columns:
                data_summary['total_visits'] = df_history['visit_count'].sum()
        
        # 확장 프로그램 데이터 처리
        extension_files = [f for f in os.listdir(uploads_dir) if f.startswith('chrome_extensions_') and f.endswith('.csv')]
        if extension_files:
            latest_extensions = max(extension_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_extensions = pd.read_csv(os.path.join(uploads_dir, latest_extensions))
            
            if 'category' in df_extensions.columns:
                data_summary['extensions'] = df_extensions['category'].value_counts().to_dict()
        
        # 설치된 프로그램 데이터 처리
        program_files = [f for f in os.listdir(uploads_dir) if f.startswith('installed_programs_') and f.endswith('.csv')]
        if program_files:
            latest_programs = max(program_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_programs = pd.read_csv(os.path.join(uploads_dir, latest_programs))
            
            if 'category' in df_programs.columns:
                data_summary['software_categories'] = df_programs['category'].value_counts().to_dict()
            data_summary['total_programs'] = len(df_programs)
        
        # 최근 파일 데이터 처리
        recent_files = [f for f in os.listdir(uploads_dir) if f.startswith('recent_files_') and f.endswith('.csv')]
        if recent_files:
            latest_recent = max(recent_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_recent = pd.read_csv(os.path.join(uploads_dir, latest_recent))
            
            if 'category' in df_recent.columns:
                data_summary['recent_files'] = df_recent['category'].value_counts().to_dict()
        
        # 네트워크 정보 처리
        network_files = [f for f in os.listdir(uploads_dir) if f.startswith('network_info_') and f.endswith('.csv')]
        if network_files:
            latest_network = max(network_files, key=lambda f: os.path.getctime(os.path.join(uploads_dir, f)))
            df_network = pd.read_csv(os.path.join(uploads_dir, latest_network))
            
            if 'category' in df_network.columns:
                data_summary['network_stats'] = df_network['category'].value_counts().to_dict()
    
    except Exception as e:
        print(f"데이터 준비 중 오류: {e}")
    
    # numpy 타입을 JSON 직렬화 가능한 타입으로 변환
    return convert_numpy_types(data_summary)

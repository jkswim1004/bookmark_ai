"""
인터랙티브 HTML 보고서 생성 함수
웹페이지와 동일한 차트가 포함된 HTML 생성
"""
import json
from datetime import datetime

def generate_interactive_analysis_html(analysis_data):
    """분석 결과 HTML 생성 - 인터랙티브 차트 포함"""
    timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')
    
    # 실제 분석 페이지와 동일한 HTML 생성
    html_template = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📈 디지털 패턴 분석 리포트 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
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
        .analysis-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #667eea;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            min-height: 400px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
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
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .insight-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 15px 0;
        }}
        .insight-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .report-header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .report-header h2 {{
            margin: 0;
            font-size: 1.8em;
        }}
        .report-header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        @media (max-width: 768px) {{
            .chart-grid {{
                grid-template-columns: 1fr;
            }}
            .container {{
                padding: 20px;
            }}
        }}
    </style>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>📈 디지털 패턴 분석 결과</h1>
        
        <div class="report-header">
            <h2>🎯 개인 디지털 패턴 분석 리포트</h2>
            <p>생성일시: {timestamp}</p>
            <p>이 보고서는 수집된 데이터를 바탕으로 개인의 디지털 사용 패턴을 분석한 결과입니다.</p>
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
                <div class="stat-number">{analysis_data.get('stats', {}).get('categories', 0)}</div>
                <div class="stat-label">주요 카테고리</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('total_visits', 0)}</div>
                <div class="stat-label">총 방문 횟수</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis_data.get('stats', {}).get('avg_daily', 0)}</div>
                <div class="stat-label">일평균 방문</div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="analysis-section">
                <h3>🔖 북마크 카테고리 분석</h3>
                <div class="chart-container">
                    <div id="bookmarkChart"></div>
                </div>
            </div>
        
            <div class="analysis-section">
                <h3>🌐 브라우저 사용 패턴</h3>
                <div class="chart-container">
                    <div id="historyChart"></div>
                </div>
            </div>
        </div>
        
        <div class="analysis-section">
            <h3>💻 시스템 구성 분석</h3>
            <div class="chart-container">
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
            <div id="aiInsights">
                <div class="insight-card">
                    <div class="insight-title">🔍 기본 패턴 분석</div>
                    <p>수집된 데이터를 바탕으로 기본적인 사용 패턴을 분석했습니다.</p>
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
        
        <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <p style="color: #6c757d; margin: 0;">
                📄 이 보고서는 <strong>신입사원 디지털 패턴 분석 시스템</strong>에서 생성되었습니다.<br>
                생성일시: {timestamp}
            </p>
        </div>
    </div>
    
    <script>
        // 페이지 로드 시 차트 생성
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('HTML 보고서 로드됨');
            
            // Plotly 라이브러리 로딩 확인
            if (typeof Plotly === 'undefined') {{
                console.error('Plotly 라이브러리가 로드되지 않았습니다');
                return;
            }}
            
            console.log('Plotly 라이브러리 로드됨');
            
            // 차트 데이터 준비
            const analysisData = {json.dumps(analysis_data, ensure_ascii=False, indent=2)};
            
            // 차트 생성
            createBookmarkChart(analysisData.bookmarks);
            createHistoryChart(analysisData.history);
            createSystemChart(analysisData.system);
            createTimeChart(analysisData.timePattern);
            
            // AI 분석 결과가 있으면 표시
            if (analysisData.ai_analysis) {{
                displayAIInsights(analysisData.ai_analysis);
                console.log('AI 분석 결과 표시됨');
            }} else {{
                console.log('AI 분석 결과 없음');
            }}
            
            console.log('모든 차트 생성 완료');
        }});
        
        function createBookmarkChart(bookmarkData) {{
            try {{
                const categories = bookmarkData?.categories || ['Development', 'Entertainment', 'Cloud', 'Education', 'Professional', 'Shopping'];
                const counts = bookmarkData?.counts || [6, 2, 2, 2, 2, 1];
                
                var data = [{{
                    values: counts,
                    labels: categories,
                    type: 'pie',
                    hole: 0.4,
                    marker: {{
                        colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b']
                    }},
                    textinfo: 'label+percent',
                    textposition: 'outside'
                }}];
                
                var layout = {{
                    title: {{
                        text: '북마크 카테고리 분포',
                        font: {{ size: 16, family: 'Segoe UI, sans-serif' }}
                    }},
                    showlegend: true,
                    legend: {{ orientation: 'h', y: -0.1 }},
                    margin: {{ t: 50, b: 50, l: 50, r: 50 }},
                    height: 400
                }};
                
                Plotly.newPlot('bookmarkChart', data, layout, {{responsive: true}});
            }} catch (error) {{
                console.error('북마크 차트 생성 오류:', error);
            }}
        }}
        
        function createHistoryChart(historyData) {{
            try {{
                const sites = historyData?.sites || ['Google', 'YouTube', 'Stack Overflow', 'AWS Console', 'GitHub', 'Netflix', 'AWS Docs', 'Reddit', 'W3Schools', 'MDN'];
                const visits = historyData?.visits || [45, 35, 25, 22, 20, 18, 16, 14, 11, 10];
                
                var data = [{{
                    x: sites,
                    y: visits,
                    type: 'bar',
                    marker: {{
                        color: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140', '#a8edea', '#fed6e3'],
                        line: {{ color: 'rgba(0,0,0,0.1)', width: 1 }}
                    }}
                }}];
                
                var layout = {{
                    title: {{
                        text: '사이트별 방문 횟수 (Top 10)',
                        font: {{ size: 16, family: 'Segoe UI, sans-serif' }}
                    }},
                    xaxis: {{ 
                        title: '웹사이트',
                        tickangle: -45
                    }},
                    yaxis: {{ title: '방문 횟수' }},
                    margin: {{ t: 50, b: 100, l: 50, r: 50 }},
                    height: 400
                }};
                
                Plotly.newPlot('historyChart', data, layout, {{responsive: true}});
            }} catch (error) {{
                console.error('히스토리 차트 생성 오류:', error);
            }}
        }}
        
        function createSystemChart(systemData) {{
            try {{
                const categories = systemData?.categories || ['Software', 'Memory', 'CPU', 'Storage', 'Network', 'Process', 'Security', 'Monitoring'];
                const counts = systemData?.counts || [4, 4, 2, 2, 2, 2, 1, 1];
                
                var data = [{{
                    values: counts,
                    labels: categories,
                    type: 'pie',
                    hole: 0.3,
                    marker: {{
                        colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#fa709a', '#fee140']
                    }},
                    textinfo: 'label+percent',
                    textposition: 'auto'
                }}];
                
                var layout = {{
                    title: {{
                        text: '시스템 정보 카테고리 분포',
                        font: {{ size: 16, family: 'Segoe UI, sans-serif' }}
                    }},
                    showlegend: true,
                    legend: {{ orientation: 'h', y: -0.1 }},
                    margin: {{ t: 50, b: 50, l: 50, r: 50 }},
                    height: 400
                }};
                
                Plotly.newPlot('systemChart', data, layout, {{responsive: true}});
            }} catch (error) {{
                console.error('시스템 차트 생성 오류:', error);
            }}
        }}
        
        function createTimeChart(timeData) {{
            try {{
                const hours = timeData?.hours || ['00-02', '02-04', '04-06', '06-08', '08-10', '10-12', '12-14', '14-16', '16-18', '18-20', '20-22', '22-24'];
                const activities = timeData?.activities || [2, 1, 0, 3, 8, 15, 12, 25, 22, 18, 12, 6];
                
                var data = [{{
                    x: hours,
                    y: activities,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {{
                        color: '#667eea',
                        width: 3,
                        shape: 'spline'
                    }},
                    marker: {{
                        color: '#764ba2',
                        size: 8,
                        line: {{ color: 'white', width: 2 }}
                    }},
                    fill: 'tonexty',
                    fillcolor: 'rgba(102, 126, 234, 0.1)'
                }}];
                
                var layout = {{
                    title: {{
                        text: '시간대별 웹 활동 패턴',
                        font: {{ size: 16, family: 'Segoe UI, sans-serif' }}
                    }},
                    xaxis: {{ 
                        title: '시간대',
                        type: 'category',
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    yaxis: {{ 
                        title: '활동 횟수',
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    margin: {{ t: 50, b: 50, l: 50, r: 50 }},
                    height: 400
                }};
                
                Plotly.newPlot('timeChart', data, layout, {{responsive: true}});
            }} catch (error) {{
                console.error('시간대별 차트 생성 오류:', error);
            }}
        }}
        
        function displayAIInsights(analysisResult) {{
            const insightsContainer = document.getElementById('aiInsights');
            
            let html = '';
            
            // AI 인사이트 표시
            if (analysisResult.ai_insights) {{
                const insights = analysisResult.ai_insights;
                
                html += `
                    <div class="insight-card">
                        <div class="insight-title">🤖 AI 종합 분석</div>
                        <p><strong>전반적 성향:</strong> ${{insights.overview || '분석 중...'}}</p>
                        <p><strong>주요 강점:</strong> ${{insights.strengths || '분석 중...'}}</p>
                        <p><strong>업무 스타일:</strong> ${{insights.work_style || '분석 중...'}}</p>
                        <p><strong>관심 분야:</strong> ${{insights.interests || '분석 중...'}}</p>
                    </div>
                `;
            }}
            
            // MBTI 분석 표시
            if (analysisResult.mbti_analysis) {{
                const mbti = analysisResult.mbti_analysis;
                
                html += `
                    <div class="insight-card">
                        <div class="insight-title">🧠 MBTI 성향 분석</div>
                        <p><strong>예상 유형:</strong> ${{mbti.predicted_type || 'ESTJ'}} (신뢰도: ${{mbti.confidence || 60}}%)</p>
                        <div style="margin-top: 15px;">
                            <div style="margin: 10px 0;">
                                <strong>외향성(E) vs 내향성(I):</strong> ${{mbti.E_I?.score || 60}}% → ${{mbti.E_I?.tendency || 'E'}}
                                <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${{mbti.E_I?.score || 60}}%; border-radius: 4px;"></div>
                                </div>
                            </div>
                            <div style="margin: 10px 0;">
                                <strong>감각(S) vs 직관(N):</strong> ${{mbti.S_N?.score || 45}}% → ${{mbti.S_N?.tendency || 'S'}}
                                <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${{mbti.S_N?.score || 45}}%; border-radius: 4px;"></div>
                                </div>
                            </div>
                            <div style="margin: 10px 0;">
                                <strong>사고(T) vs 감정(F):</strong> ${{mbti.T_F?.score || 65}}% → ${{mbti.T_F?.tendency || 'T'}}
                                <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${{mbti.T_F?.score || 65}}%; border-radius: 4px;"></div>
                                </div>
                            </div>
                            <div style="margin: 10px 0;">
                                <strong>판단(J) vs 인식(P):</strong> ${{mbti.J_P?.score || 55}}% → ${{mbti.J_P?.tendency || 'J'}}
                                <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: ${{mbti.J_P?.score || 55}}%; border-radius: 4px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }}
            
            // 성격 특성 표시
            if (analysisResult.personality_traits) {{
                const traits = analysisResult.personality_traits;
                
                html += `
                    <div class="insight-card">
                        <div class="insight-title">🎯 성격 특성 분석</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                            <div>
                                <strong>개방성:</strong> ${{traits.openness?.score || 70}}%<br>
                                <small>${{traits.openness?.description || '새로운 경험에 대한 개방성'}}</small>
                            </div>
                            <div>
                                <strong>성실성:</strong> ${{traits.conscientiousness?.score || 65}}%<br>
                                <small>${{traits.conscientiousness?.description || '조직적이고 계획적인 성향'}}</small>
                            </div>
                            <div>
                                <strong>외향성:</strong> ${{traits.extraversion?.score || 60}}%<br>
                                <small>${{traits.extraversion?.description || '사교적이고 활동적인 성향'}}</small>
                            </div>
                            <div>
                                <strong>친화성:</strong> ${{traits.agreeableness?.score || 70}}%<br>
                                <small>${{traits.agreeableness?.description || '협력적이고 신뢰하는 성향'}}</small>
                            </div>
                            <div>
                                <strong>창의성:</strong> ${{traits.creativity?.score || 75}}%<br>
                                <small>${{traits.creativity?.description || '창의적 사고와 혁신성'}}</small>
                            </div>
                            <div>
                                <strong>기술 친화도:</strong> ${{traits.tech_savviness?.score || 80}}%<br>
                                <small>${{traits.tech_savviness?.description || '기술 수용과 활용 능력'}}</small>
                            </div>
                        </div>
                    </div>
                `;
            }}
            
            // 추천 사항 표시
            if (analysisResult.recommendations) {{
                const rec = analysisResult.recommendations;
                
                html += `
                    <div class="insight-card">
                        <div class="insight-title">💡 개인화된 추천</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
                            <div>
                                <h4 style="margin: 0 0 10px 0; color: #667eea;">🛠️ 생산성 도구</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    ${{(rec.productivity_tools || []).map(item => `<li>${{item}}</li>`).join('')}}
                                </ul>
                            </div>
                            <div>
                                <h4 style="margin: 0 0 10px 0; color: #667eea;">📚 학습 리소스</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    ${{(rec.learning_resources || []).map(item => `<li>${{item}}</li>`).join('')}}
                                </ul>
                            </div>
                            <div>
                                <h4 style="margin: 0 0 10px 0; color: #667eea;">💻 소프트웨어/앱</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    ${{(rec.software_apps || []).map(item => `<li>${{item}}</li>`).join('')}}
                                </ul>
                            </div>
                            <div>
                                <h4 style="margin: 0 0 10px 0; color: #667eea;">🚀 커리어 발전</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    ${{(rec.career_development || []).map(item => `<li>${{item}}</li>`).join('')}}
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
            }}
            
            // AI 분석 여부 표시
            const aiPowered = analysisResult.ai_powered;
            html += `
                <div class="insight-card" style="background: ${{aiPowered ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' : 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'}};;">
                    <div class="insight-title" style="color: white;">
                        ${{aiPowered ? '🤖 OpenAI 기반 분석' : '📊 기본 분석'}}
                    </div>
                    <p style="color: white; margin: 0;">
                        ${{aiPowered 
                            ? 'OpenAI GPT를 사용하여 고도화된 AI 분석을 수행했습니다.' 
                            : 'OpenAI API 키 없이 기본 분석을 수행했습니다.'
                        }}
                    </p>
                </div>
            `;
            
            insightsContainer.innerHTML = html;
        }}
    </script>
</body>
</html>'''
    
    return html_template

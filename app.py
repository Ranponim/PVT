import os
import json
import logging
import sys
from datetime import datetime
import pandas as pd

# 로그 설정
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename=f'logs/mcp_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# 파일 로딩 함수
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        logging.info(f"파일 {file_path} 읽기 성공: {data}")
        return data
    except Exception as e:
        logging.error(f"파일 {file_path} 읽기 실패: {str(e)}")
        return None

# KPI 비교 및 분석 함수
def analyze_kpi_comparison(n1_data, n_data):
    analysis_results = {
        "peg_comparisons": {},
        "performance_impact": {},
        "recommendations": [],
        "overall_assessment": ""
    }
    all_pegs = set(n1_data.keys()) | set(n_data.keys())
    for peg in all_pegs:
        if peg not in n1_data or peg not in n_data:
            continue
        n1_peg_data = n1_data[peg]
        n_peg_data = n_data[peg]
        comparisons = []
        for n1_item in n1_peg_data:
            cell_name = n1_item['cell_name']
            period = n1_item['period']
            n_item = next((item for item in n_peg_data 
                          if item['cell_name'] == cell_name and item['period'] == period), None)
            if n_item:
                n1_value = n1_item['avg_value']
                n_value = n_item['avg_value']
                if n1_value != 0:
                    change_percent = ((n_value - n1_value) / n1_value) * 100
                else:
                    change_percent = float('inf') if n_value > 0 else 0
                comparison = {
                    "cell_name": cell_name,
                    "period": period,
                    "n1_value": n1_value,
                    "n_value": n_value,
                    "change_percent": round(change_percent, 2),
                    "trend": "증가" if change_percent > 0 else "감소" if change_percent < 0 else "동일"
                }
                comparisons.append(comparison)
        analysis_results["peg_comparisons"][peg] = comparisons
        if comparisons:
            avg_change = sum(abs(c['change_percent']) for c in comparisons) / len(comparisons)
            max_change = max(abs(c['change_percent']) for c in comparisons)
            impact_analysis = analyze_performance_impact(peg, avg_change, max_change)
            analysis_results["performance_impact"][peg] = impact_analysis
            if max_change > 20:
                analysis_results["recommendations"].append({
                    "peg": peg,
                    "reason": f"변화폭이 큽니다 (최대 {max_change:.1f}%)",
                    "priority": "높음" if max_change > 50 else "중간"
                })
    analysis_results["overall_assessment"] = generate_overall_assessment(analysis_results)
    return analysis_results

def analyze_performance_impact(peg, avg_change, max_change):
    impact = {
        "severity": "낮음",
        "description": "",
        "action_needed": False
    }
    if max_change > 50:
        impact["severity"] = "높음"
        impact["description"] = f"{peg}의 변화가 매우 큽니다. 즉시 검토가 필요합니다."
        impact["action_needed"] = True
    elif max_change > 20:
        impact["severity"] = "중간"
        impact["description"] = f"{peg}의 변화가 중간 수준입니다. 주의 깊게 모니터링이 필요합니다."
        impact["action_needed"] = True
    else:
        impact["description"] = f"{peg}의 변화가 안정적입니다."
    return impact

def generate_overall_assessment(analysis_results):
    high_priority_count = len([r for r in analysis_results["recommendations"] if r["priority"] == "높음"])
    medium_priority_count = len([r for r in analysis_results["recommendations"] if r["priority"] == "중간"])
    assessment = f"전체 {len(analysis_results['peg_comparisons'])}개 PEG 분석 결과:\n"
    assessment += f"- 높은 우선순위 검토 필요: {high_priority_count}개\n"
    assessment += f"- 중간 우선순위 검토 필요: {medium_priority_count}개\n"
    if high_priority_count > 0:
        assessment += "\n⚠️ 즉시 조치가 필요한 PEG가 있습니다."
    elif medium_priority_count > 0:
        assessment += "\n⚠️ 주의 깊게 모니터링이 필요한 PEG가 있습니다."
    else:
        assessment += "\n✅ 모든 PEG가 안정적으로 운영되고 있습니다."
    return assessment

def prepare_chart_data(n1_data, n_data):
    """PEG별로 period, n1, n, diff_percent 데이터 구조화"""
    peg_chart_data = {}
    all_pegs = set(n1_data.keys()) | set(n_data.keys())
    for peg in all_pegs:
        if peg not in n1_data or peg not in n_data:
            continue
        n1_peg_data = n1_data[peg]
        n_peg_data = n_data[peg]
        periods = []
        n1_values = []
        n_values = []
        diff_percent = []
        for n1_item in n1_peg_data:
            cell_name = n1_item['cell_name']
            period = n1_item['period']
            n_item = next((item for item in n_peg_data 
                          if item['cell_name'] == cell_name and item['period'] == period), None)
            if n_item:
                n1_value = n1_item['avg_value']
                n_value = n_item['avg_value']
                if n1_value != 0:
                    change_percent = ((n_value - n1_value) / n1_value) * 100
                else:
                    change_percent = float('inf') if n_value > 0 else 0
                periods.append(f"{cell_name}-{period}")
                n1_values.append(n1_value)
                n_values.append(n_value)
                diff_percent.append(round(change_percent, 2))
        peg_chart_data[peg] = {
            "periods": periods,
            "n1": n1_values,
            "n": n_values,
            "diff_percent": diff_percent
        }
    return peg_chart_data

# HTML 리포트 템플릿 (Plotly.js 기반)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>KPI 분석 리포트</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: 'Malgun Gothic', Arial, sans-serif; margin: 40px; }
        .select-area { margin-bottom: 20px; }
        .chart-area { width: 100%; max-width: 1200px; margin: auto; }
    </style>
</head>
<body>
    <h1>KPI 분석 리포트</h1>
    <div class="select-area">
        <label>PEG 선택 (최대 4개): </label>
        <select id="peg-select" multiple size="5">
            {% for peg in peg_chart_data.keys() %}
            <option value="{{ peg }}">{{ peg }}</option>
            {% endfor %}
        </select>
        <label>그래프 종류: </label>
        <select id="chart-type">
            <option value="line">꺾은선(차분%)</option>
            <option value="bar">막대(n-1/n avg)</option>
        </select>
        <label>보조축 사용: </label>
        <input type="checkbox" id="secondary-axis">
        <button onclick="drawChart()">그래프 그리기</button>
    </div>
    <div class="chart-area">
        <div id="chart"></div>
    </div>
    <script>
        const pegChartData = {{ peg_chart_data | tojson }};
        function drawChart() {
            const selected = Array.from(document.getElementById('peg-select').selectedOptions).map(o => o.value).slice(0,4);
            const chartType = document.getElementById('chart-type').value;
            const useSecondary = document.getElementById('secondary-axis').checked;
            let data = [];
            let layout = { title: 'PEG KPI 비교', xaxis: {title: 'Cell-Period'}, yaxis: {title: ''} };
            if (chartType === 'line') {
                layout.yaxis.title = '차분(%)';
                selected.forEach((peg, idx) => {
                    data.push({
                        x: pegChartData[peg].periods,
                        y: pegChartData[peg].diff_percent,
                        name: peg,
                        type: 'scatter',
                        yaxis: (useSecondary && idx === 1) ? 'y2' : 'y'
                    });
                });
                if (useSecondary && selected.length > 1) {
                    layout.yaxis2 = { title: '보조축(%)', overlaying: 'y', side: 'right' };
                }
            } else {
                layout.yaxis.title = '평균값';
                selected.forEach((peg, idx) => {
                    data.push({
                        x: pegChartData[peg].periods,
                        y: pegChartData[peg].n1,
                        name: peg + ' (n-1)',
                        type: 'bar',
                        marker: {color: 'rgba(55,128,191,0.7)'},
                        yaxis: (useSecondary && idx === 1) ? 'y2' : 'y'
                    });
                    data.push({
                        x: pegChartData[peg].periods,
                        y: pegChartData[peg].n,
                        name: peg + ' (n)',
                        type: 'bar',
                        marker: {color: 'rgba(255,153,51,0.7)'},
                        yaxis: (useSecondary && idx === 1) ? 'y2' : 'y'
                    });
                });
                if (useSecondary && selected.length > 1) {
                    layout.yaxis2 = { title: '보조축(평균값)', overlaying: 'y', side: 'right' };
                }
                layout.barmode = 'group';
            }
            Plotly.newPlot('chart', data, layout);
        }
    </script>
</body>
</html>
'''

def save_html_report(analysis, peg_chart_data, output_path=None):
    if not os.path.exists("output"):
        os.makedirs("output")
    if output_path is None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        output_path = f"output/report_{timestamp}.html"
    
    # Jinja2 대신 간단한 문자열 치환 사용
    html_content = HTML_TEMPLATE
    
    # PEG 옵션 생성
    peg_options = ""
    for peg in peg_chart_data.keys():
        peg_options += f'<option value="{peg}">{peg}</option>\n'
    
    # pegChartData JSON 생성
    peg_chart_json = json.dumps(peg_chart_data, ensure_ascii=False)
    
    # 템플릿 치환
    html_content = html_content.replace('{% for peg in peg_chart_data.keys() %}\n            <option value="{{ peg }}">{{ peg }}</option>\n            {% endfor %}', peg_options)
    html_content = html_content.replace('{{ peg_chart_data | tojson }}', peg_chart_json)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return output_path

def save_excel_report(analysis, peg_chart_data, output_path=None):
    if not os.path.exists("output"):
        os.makedirs("output")
    if output_path is None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        output_path = f"output/report_{timestamp}.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for peg, chart in peg_chart_data.items():
            df = pd.DataFrame({
                'Period': chart['periods'],
                'n-1': chart['n1'],
                'n': chart['n'],
                '차분(%)': chart['diff_percent']
            })
            df.to_excel(writer, sheet_name=peg[:31], index=False)
    return output_path

def analyze_pegs(n1_path, n_path):
    """stdio 방식으로 KPI 분석을 수행하는 메인 함수"""
    try:
        logging.info(f"입력 경로: n1_path={n1_path}, n_path={n_path}")
        
        if not n1_path or not n_path:
            msg = "n1_path와 n_path를 모두 입력해야 합니다."
            logging.error(msg)
            return {"status": "error", "message": msg}
        
        n1_data = load_json_file(n1_path)
        n_data = load_json_file(n_path)
        
        if n1_data is None or n_data is None:
            msg = "파일을 읽는 데 실패했습니다."
            logging.error(msg)
            return {"status": "error", "message": msg}
        
        analysis_results = analyze_kpi_comparison(n1_data, n_data)
        logging.info(f"분석 결과: {analysis_results}")
        
        peg_chart_data = prepare_chart_data(n1_data, n_data)
        html_path = save_html_report(analysis_results, peg_chart_data)
        excel_path = save_excel_report(analysis_results, peg_chart_data)
        
        logging.info(f"HTML 리포트 저장: {html_path}")
        logging.info(f"Excel 리포트 저장: {excel_path}")
        
        return {
            "status": "success",
            "message": "KPI 비교 및 분석 및 리포트 생성 완료",
            "analysis": analysis_results,
            "html_report": html_path,
            "excel_report": excel_path
        }
    except Exception as e:
        logging.error(f"에러 발생: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    """stdio 방식 메인 함수"""
    try:
        # stdin에서 JSON 입력 읽기
        input_data = sys.stdin.read()
        request_data = json.loads(input_data)
        
        n1_path = request_data.get('n1_path')
        n_path = request_data.get('n_path')
        
        # 분석 실행
        result = analyze_pegs(n1_path, n_path)
        
        # 결과를 stdout으로 출력
        reconfig = getattr(sys.stdout, 'reconfigure', None)
        if callable(reconfig):
            reconfig(encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except json.JSONDecodeError as e:
        error_result = {"status": "error", "message": f"JSON 파싱 오류: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {"status": "error", "message": f"예상치 못한 오류: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
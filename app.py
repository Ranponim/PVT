from flask import Flask, request, jsonify
import logging
import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import pandas as pd

# 로그 설정
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename=f'logs/mcp_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

app = Flask(__name__)

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"파일 {file_path} 읽기 성공: {data}")
        return data
    except Exception as e:
        logging.error(f"파일 {file_path} 읽기 실패: {str(e)}")
        return None

def analyze_kpi_comparison(n1_data, n_data):
    """KPI 비교 및 분석"""
    analysis_results = {
        "peg_comparisons": {},
        "performance_impact": {},
        "recommendations": [],
        "overall_assessment": ""
    }
    
    # 모든 peg에 대해 비교
    all_pegs = set(n1_data.keys()) | set(n_data.keys())
    
    for peg in all_pegs:
        if peg not in n1_data or peg not in n_data:
            continue
            
        n1_peg_data = n1_data[peg]
        n_peg_data = n_data[peg]
        
        # cell과 period별로 매칭하여 비교
        comparisons = []
        for n1_item in n1_peg_data:
            cell_name = n1_item['cell_name']
            period = n1_item['period']
            
            # n 데이터에서 같은 cell, period 찾기
            n_item = next((item for item in n_peg_data 
                          if item['cell_name'] == cell_name and item['period'] == period), None)
            
            if n_item:
                n1_value = n1_item['avg_value']
                n_value = n_item['avg_value']
                
                # 변화율 계산
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
        
        # 성능 영향 분석
        if comparisons:
            avg_change = sum(abs(c['change_percent']) for c in comparisons) / len(comparisons)
            max_change = max(abs(c['change_percent']) for c in comparisons)
            
            impact_analysis = analyze_performance_impact(peg, avg_change, max_change)
            analysis_results["performance_impact"][peg] = impact_analysis
            
            # 추천 사항
            if max_change > 20:  # 20% 이상 변화
                analysis_results["recommendations"].append({
                    "peg": peg,
                    "reason": f"변화폭이 큽니다 (최대 {max_change:.1f}%)",
                    "priority": "높음" if max_change > 50 else "중간"
                })
    
    # 종합 평가
    analysis_results["overall_assessment"] = generate_overall_assessment(analysis_results)
    
    return analysis_results

def analyze_performance_impact(peg, avg_change, max_change):
    """KPI 변화가 시스템 성능에 미치는 영향 분석"""
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
    """종합 Cell 성능 평가 및 분석"""
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

def generate_expert_analysis(peg, comparisons):
    """3GPP 이동통신 전문가 LLM 분석 코멘트 생성"""
    if not comparisons:
        return "분석할 데이터가 없습니다."
    
    # PEG별 전문 분석 로직
    peg_analysis = {
        "peg_A": {
            "description": "PEG_A는 일반적으로 연결 성공률과 관련된 지표입니다.",
            "good_range": "95% 이상",
            "warning_threshold": "90% 미만",
            "critical_threshold": "85% 미만"
        },
        "peg_B": {
            "description": "PEG_B는 통화 품질과 관련된 지표입니다.",
            "good_range": "98% 이상", 
            "warning_threshold": "95% 미만",
            "critical_threshold": "90% 미만"
        }
    }
    
    analysis = peg_analysis.get(peg, {
        "description": f"{peg}는 이동통신 네트워크 성능 지표입니다.",
        "good_range": "기준값 이상",
        "warning_threshold": "기준값의 90%",
        "critical_threshold": "기준값의 80%"
    })
    
    # 변화율 분석
    changes = [abs(c['change_percent']) for c in comparisons]
    avg_change = sum(changes) / len(changes)
    max_change = max(changes)
    
    expert_comment = f""" {peg} 전문 분석

 기본 정보:
- {analysis['description']}
- 권장 범위: {analysis['good_range']}
- 주의 임계값: {analysis['warning_threshold']}
- 위험 임계값: {analysis['critical_threshold']}

 변화 분석:
- 평균 변화율: {avg_change:.1f}%
- 최대 변화율: {max_change:.1f}%

 디버깅 포인트:
"""
    
    if max_change > 50:
        expert_comment += """- ⚠️ 급격한 변화 감지: 네트워크 설정 변경 확인 필요
-  장비 상태 점검 필요
- 📊 트래픽 패턴 분석 필요"""
    elif max_change > 20:
        expert_comment += """- ⚠️ 중간 수준 변화: 정기 모니터링 강화
-  주변 셀 간섭 확인
- 📊 시간대별 패턴 분석"""
    else:
        expert_comment += """- ✅ 안정적인 운영 상태
-  정상 범위 내 변화
- 📊 지속적인 모니터링 권장"""
    
    return expert_comment

def prepare_chart_data(peg_comparisons):
    """차트 데이터 준비"""
    chart_data = {}
    
    for peg, comparisons in peg_comparisons.items():
        labels = [f"{comp['cell_name']}-{comp['period']}" for comp in comparisons]
        n1_values = [comp['n1_value'] for comp in comparisons]
        n_values = [comp['n_value'] for comp in comparisons]
        change_percentages = [comp['change_percent'] for comp in comparisons]
        
        chart_data[peg] = {
            'labels': labels,
            'n1_values': n1_values,
            'n_values': n_values,
            'change_percentages': change_percentages
        }
    
    return chart_data

def save_html_report(analysis, output_path=None):
    """HTML 리포트 생성"""
    if not os.path.exists("output"):
        os.makedirs("output")
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        output_path = f"output/report_{timestamp}.html"
    
    # 전문가 분석 생성
    expert_analysis = {}
    for peg in analysis["peg_comparisons"].keys():
        expert_analysis[peg] = generate_expert_analysis(peg, analysis["peg_comparisons"][peg])
    
    # 차트 데이터 준비
    chart_data = prepare_chart_data(analysis["peg_comparisons"])
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")
    
    html = template.render(
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        overall_assessment=analysis["overall_assessment"],
        recommendations=analysis["recommendations"],
        peg_comparisons=analysis["peg_comparisons"],
        performance_impact=analysis["performance_impact"],
        expert_analysis=expert_analysis,
        chart_data=chart_data
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    logging.info(f"HTML 리포트 생성 완료: {output_path}")
    return output_path

def save_excel_report(analysis, output_path=None):
    """Excel 리포트 생성"""
    if not os.path.exists("output"):
        os.makedirs("output")
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        output_path = f"output/report_{timestamp}.xlsx"
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # PEG별 KPI 변화
        for peg, comps in analysis["peg_comparisons"].items():
            df = pd.DataFrame(comps)
            df.to_excel(writer, sheet_name=peg, index=False)
        
        # 추천 사항
        if analysis["recommendations"]:
            recs = pd.DataFrame(analysis["recommendations"])
            recs.to_excel(writer, sheet_name="추천사항", index=False)
        
        # 종합 평가
        summary = pd.DataFrame([{"종합평가": analysis["overall_assessment"]}])
        summary.to_excel(writer, sheet_name="종합평가", index=False)
    
    logging.info(f"Excel 리포트 생성 완료: {output_path}")
    return output_path

@app.route('/tool_analyze_all_pegs_post', methods=['POST'])
def analyze_pegs():
    try:
        req = request.get_json()
        logging.info(f"입력 JSON: {req}")

        n1_path = req.get('n1_path')
        n_path = req.get('n_path')

        if not n1_path or not n_path:
            msg = "n1_path와 n_path를 모두 입력해야 합니다."
            logging.error(msg)
            return jsonify({"status": "error", "message": msg}), 400

        n1_data = load_json_file(n1_path)
        n_data = load_json_file(n_path)

        if n1_data is None or n_data is None:
            msg = "파일을 읽는 데 실패했습니다."
            logging.error(msg)
            return jsonify({"status": "error", "message": msg}), 400

        # KPI 비교 및 분석
        analysis_results = analyze_kpi_comparison(n1_data, n_data)
        logging.info(f"분석 결과: {analysis_results}")

        # 리포트 생성
        html_path = save_html_report(analysis_results)
        xls_path = save_excel_report(analysis_results)

        return jsonify({
            "status": "success", 
            "message": "KPI 비교 및 분석 완료",
            "analysis": analysis_results,
            "html_report": html_path,
            "xls_report": xls_path
        })

    except Exception as e:
        logging.error(f"에러 발생: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
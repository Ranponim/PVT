import subprocess
import json
import sys

def test_stdio_analysis():
    """stdio 방식으로 app.py를 테스트하는 함수"""
    
    # 테스트용 입력 데이터
    test_input = {
        "n1_path": "data/n1.json",
        "n_path": "data/n.json"
    }
    
    # JSON을 문자열로 변환
    input_json = json.dumps(test_input, ensure_ascii=False)
    
    try:
        # subprocess로 app.py 실행
        result = subprocess.run(
            [sys.executable, "app.py"],
            input=input_json,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        
        print("=== 실행 결과 ===")
        print(f"Return Code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
            
        # 결과 파싱
        if result.stdout:
            try:
                output_data = json.loads(result.stdout)
                print(f"\n=== 파싱된 결과 ===")
                print(f"Status: {output_data.get('status')}")
                print(f"Message: {output_data.get('message')}")
                if output_data.get('status') == 'success':
                    print(f"HTML Report: {output_data.get('html_report')}")
                    print(f"Excel Report: {output_data.get('excel_report')}")
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                
    except Exception as e:
        print(f"실행 오류: {e}")

if __name__ == "__main__":
    test_stdio_analysis() 
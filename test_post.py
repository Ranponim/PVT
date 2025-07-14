import requests

url = "http://localhost:5001/tool_analyze_all_pegs_post"
data = {
    "n1_path": "data/n1.json",
    "n_path": "data/n.json"
}

response = requests.post(url, json=data)
print(response.json())
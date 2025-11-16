import requests
import json
response = requests.get(f"http://localhost:8090/api/objects/info?name=m8&format=json")
info = json.loads(response.text)
print(info)

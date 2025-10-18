import requests
import json

url = "http://127.0.0.1:5000/signup"
headers = {"Content-Type": "application/json"}
data = {"email": "test1000@gmail.com", "password": "password", "username": "testuser"}

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.text)
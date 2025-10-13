import requests

files = {'file': open('test_policy.pdf', 'rb')}
response = requests.post("http://127.0.0.1:5000/recommendations/analyze", files=files)

print("Status code:", response.status_code)
print("Response text:", response.text)

# Only try to parse JSON if status_code is 200
if response.status_code == 200:
    analyze_response = response.json()
    print(analyze_response)
else:
    print("Failed to reach endpoint.")

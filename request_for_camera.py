import requests
URL="http://127.0.0.1:5050/url"
r=requests.get(url=URL)
data=r.json()
print(data)

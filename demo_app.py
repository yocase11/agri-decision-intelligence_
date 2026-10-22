import requests

data = {'crop': 'Onion', 'quantity_kg': 2000, 'lat': 11.0, 'lon': 77.0}
r = requests.post('http://127.0.0.1:8503/decide', data=data)
print('Status:', r.status_code)
print(r.text)
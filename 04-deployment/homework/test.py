import requests

rides = {
    "taxi_type": "yellow",
    "year": "2023",
    "month": "05"
}

response = requests.post('http://localhost:9696/predict', json=rides)
print(response.json())

import requests

url = "http://127.0.0.1:8000/chat"

msg = {"telefone": "123456789", "mensagem": "Quero um X-Python, sou o Lucas, moro na Rua A, tel 123"}

response = requests.post(url, json=msg)
print(response.json())
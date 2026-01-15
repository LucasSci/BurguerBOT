import os
from google import genai # O import mudou!
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 1. Configuração do Cliente (O jeito novo)
client = genai.Client(api_key=api_key)

# 2. Fazendo a chamada
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents="Você é um assistente de hamburgueria. Diga 'Olá, bem-vindo ao BurgerBot!' de forma animada."
    )
    
    print("RESPOSTA DO GEMINI:")
    print(response.text)
except Exception as e:
    print(f"Erro ao conectar: {e}")
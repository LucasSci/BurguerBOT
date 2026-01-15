from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import uvicorn
from src.chatbot import BurgerBrain # Importando nosso cérebro novo

load_dotenv()

app = FastAPI(title="BurgerBot Server")

# Instancia o cérebro uma única vez
bot = BurgerBrain()

@app.post("/sms")
async def reply_whatsapp(Body: str = Form(...), From: str = Form(...)):
    # Limpa o número (remove "whatsapp:")
    numero_cliente = From.replace("whatsapp:", "")
    
    print(f"📩 Mensagem de {numero_cliente}: {Body}")

    # --- A MÁGICA ACONTECE AQUI ---
    # O servidor não sabe como responder, ele pergunta pro Brain
    resposta_texto = bot.processar_mensagem(numero_cliente, Body)
    # ------------------------------

    # Prepara resposta pro Twilio
    twiml = MessagingResponse()
    twiml.message(resposta_texto)
    return Response(content=str(twiml), media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
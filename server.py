from fastapi import FastAPI, Response, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import uvicorn
from src.chatbot import BurgerBrain # Importando nosso cérebro novo

load_dotenv()

app = FastAPI(title="BurgerBot Server")

# Instancia o cérebro uma única vez
bot = BurgerBrain()

@app.get("/")
async def root():
    return {"status": "ok", "message": "BurgerBot ativo. Use POST /sms para mensagens."}

@app.post("/sms")
async def reply_whatsapp(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        payload = await request.form()
        body = payload.get("Body")
        sender = payload.get("From")
    else:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Payload inválido.") from exc
        body = payload.get("Body") or payload.get("body") or payload.get("message")
        sender = payload.get("From") or payload.get("from") or payload.get("sender")

    if not body or not sender:
        raise HTTPException(status_code=400, detail="Body e From são obrigatórios.")

    # Limpa o número (remove "whatsapp:")
    numero_cliente = sender.replace("whatsapp:", "")
    
    print(f"📩 Mensagem de {numero_cliente}: {body}")

    # --- A MÁGICA ACONTECE AQUI ---
    # O servidor não sabe como responder, ele pergunta pro Brain
    resposta_texto = bot.processar_mensagem(numero_cliente, body)
    # ------------------------------

    # Prepara resposta pro Twilio
    twiml = MessagingResponse()
    twiml.message(resposta_texto)
    return Response(content=str(twiml), media_type="application/xml")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

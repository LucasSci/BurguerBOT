import os
import json
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn

# --- IMPORTAÇÕES DAS SUAS FERRAMENTAS ---
# Tenta importar de 'src.tools' (se tiver pasta) ou direto de 'tools'
try:
    from src.tools import listar_cardapio, finalizar_pedido, ItemPedidoInput
except ImportError:
    print('ERRO')

# 1. CONFIGURAÇÃO INICIAL
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# 2. MEMÓRIA DO BOT (Dicionário para guardar o histórico por número de telefone)
historico_conversas = {}

# 3. DEFINIÇÃO DAS FERRAMENTAS (Igual ao seu main_bot.py)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "listar_cardapio",
            "description": "Consulta o cardápio e retorna produtos e preços.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalizar_pedido",
            "description": "Registra o pedido final no banco de dados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_cliente": {"type": "string"},
                    "telefone": {"type": "string"},
                    "endereco": {"type": "string"},
                    "itens": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "produto": {"type": "string"},
                                "quantidade": {"type": "integer"},
                                "obs": {"type": "string"}
                            },
                            "required": ["produto", "quantidade"]
                        }
                    }
                },
                "required": ["nome_cliente", "telefone", "endereco", "itens"]
            }
        }
    }
]

# Mapa para executar as funções reais
funcoes_disponiveis = {
    "listar_cardapio": listar_cardapio,
    "finalizar_pedido": finalizar_pedido
}

@app.post("/sms")
async def reply_whatsapp(Body: str = Form(...), From: str = Form(...)):
    """
    Recebe mensagem do WhatsApp, processa com GPT-4 e responde.
    """
    numero_cliente = From.replace("whatsapp:", "")
    mensagem_usuario = Body

    print(f"📩 Mensagem de {numero_cliente}: {mensagem_usuario}")

    # --- 1. RECUPERA OU INICIA O HISTÓRICO DESTE CLIENTE ---
    if numero_cliente not in historico_conversas:
        historico_conversas[numero_cliente] = [
            {"role": "system", "content": """
            Você é o atendente virtual da 'DevBurger'. Seu tom é prestativo e eficiente.
            REGRAS:
            1. Use 'listar_cardapio' se o cliente perguntar preços ou opções.
            2. Não invente produtos. Use os dados do cardápio.
            3. Para fechar o pedido, você PRECISA OBRIGATORIAMENTE de: Nome, Telefone, Endereço e Itens.
            4. Antes de chamar 'finalizar_pedido', confirme o resumo e o endereço.
            5. Seja breve (limite de caracteres do WhatsApp).
            """}
        ]
    
    # Adiciona a mensagem nova ao histórico
    historico_conversas[numero_cliente].append({"role": "user", "content": mensagem_usuario})

    # --- 2. CHAMA A OPENAI ---
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=historico_conversas[numero_cliente],
            tools=tools_schema,
            tool_choice="auto"
        )
        
        msg_bot = response.choices[0].message

        # --- 3. VERIFICA SE A IA QUER USAR UMA FERRAMENTA ---
        if msg_bot.tool_calls:
            # Adiciona a intenção da IA no histórico
            historico_conversas[numero_cliente].append(msg_bot)

            for tool_call in msg_bot.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"⚙️ [IA CHAMOU]: {func_name}")
                
                # Executa a função Python real
                funcao_python = funcoes_disponiveis.get(func_name)
                
                if func_name == "finalizar_pedido":
                    # Tratamento especial para o objeto complexo de pedido
                    try:
                        itens_obj = [ItemPedidoInput(**item) for item in func_args['itens']]
                        resultado = funcao_python(
                            nome_cliente=func_args['nome_cliente'],
                            telefone=func_args['telefone'],
                            endereco=func_args['endereco'],
                            itens=itens_obj
                        )
                    except Exception as e:
                        resultado = f"Erro ao processar pedido: {str(e)}"
                else:
                    resultado = funcao_python(**func_args)

                # Devolve o resultado da ferramenta para a IA
                historico_conversas[numero_cliente].append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": str(resultado)
                })

            # Chama a IA de novo para gerar a resposta final com os dados da ferramenta
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=historico_conversas[numero_cliente]
            )
            resposta_final = final_response.choices[0].message.content
        
        else:
            # Se não chamou ferramenta, só pega a resposta texto
            resposta_final = msg_bot.content

        # Adiciona a resposta final ao histórico
        historico_conversas[numero_cliente].append({"role": "assistant", "content": resposta_final})

    except Exception as e:
        print(f"❌ Erro OpenAI: {e}")
        resposta_final = "Desculpe, tive um problema técnico no meu cérebro digital. Tente novamente!"

    # --- 4. ENVIA RESPOSTA PARA O TWILIO ---
    twiml = MessagingResponse()
    twiml.message(resposta_final)
    return Response(content=str(twiml), media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
import os
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Form
from openai import OpenAI
from dotenv import load_dotenv

from src.tools import listar_cardapio, finalizar_pedido, ItemPedidoInput

load_dotenv()

app = FastAPI(title="BurgerBot API")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Memória (Sessão)
sessions: Dict[str, List[dict]] = {}

SYSTEM_PROMPT = """
Você é o atendente virtual da 'DevBurger'.
Seu tom é prestativo, eficiente e descolado.
REGRAS:
1. Use 'listar_cardapio' se o cliente perguntar preços.
2. Não invente produtos.
3. Para fechar, EXIJA: Nome, Telefone, Endereço e Itens.
4. Confirme o pedido antes de salvar.
"""

# Schema das Ferramentas
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "listar_cardapio",
            "description": "Consulta cardápio.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalizar_pedido",
            "description": "Salva pedido no banco.",
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

FUNCOES_DISPONIVEIS = {
    "listar_cardapio": listar_cardapio,
    "finalizar_pedido": finalizar_pedido
}

# --- O ENDPOINT ADAPTADO PARA TWILIO ---
@app.post("/chat")
async def chat_endpoint(
    From: str = Form(...), # O Twilio manda o número aqui
    Body: str = Form(...)  # O Twilio manda a mensagem aqui
):
    print(f"📩 Recebido do Twilio ({From}): {Body}")
    
    phone = From
    user_msg = Body

    # 1. Recupera/Cria Histórico
    if phone not in sessions:
        sessions[phone] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    sessions[phone].append({"role": "user", "content": user_msg})

    # 2. Chama a IA
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[phone],
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )

        msg_bot = response.choices[0].message

        # 3. Processa Ferramentas (se houver)
        if msg_bot.tool_calls:
            sessions[phone].append(msg_bot) # Salva a intenção

            for tool_call in msg_bot.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"⚙️ Executando {func_name}...")
                
                func_python = FUNCOES_DISPONIVEIS.get(func_name)
                
                if func_name == "finalizar_pedido":
                    try:
                        itens_obj = [ItemPedidoInput(**item) for item in func_args['itens']]
                        resultado = func_python(
                            nome_cliente=func_args['nome_cliente'],
                            telefone=func_args['telefone'],
                            endereco=func_args['endereco'],
                            itens=itens_obj
                        )
                    except Exception as e:
                        resultado = f"Erro dados: {e}"
                else:
                    resultado = func_python(**func_args)

                sessions[phone].append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": str(resultado)
                })

            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=sessions[phone]
            )
            resposta_final = final_response.choices[0].message.content
        else:
            resposta_final = msg_bot.content

        sessions[phone].append({"role": "assistant", "content": resposta_final})
        
        # O Twilio espera apenas texto simples ou XML, mas se retornarmos string ele entende.
        return resposta_final

    except Exception as e:
        print(f"Erro: {e}")
        return "Desculpe, tive um erro interno. Tente novamente."
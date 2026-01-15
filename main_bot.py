import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from src.tools import listar_cardapio, finalizar_pedido, ItemPedidoInput

# Carrega ambiente
load_dotenv()

# Configura cliente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 1. DEFINIÇÃO DAS FERRAMENTAS (SCHEMA) ---
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "listar_cardapio",
            "description": "Consulta o cardápio e retorna produtos e preços.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
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
                    "nome_cliente": {"type": "string", "description": "Nome do cliente"},
                    "telefone": {"type": "string", "description": "Telefone do cliente"},
                    "endereco": {"type": "string", "description": "Endereço completo para entrega"},
                    "itens": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "produto": {"type": "string", "description": "Nome exato do lanche"},
                                "quantidade": {"type": "integer", "description": "Qtd"},
                                "obs": {"type": "string", "description": "Observações (opcional)"}
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

def chat_loop():
    print("🍔 BURGER-BOT (OPENAI 4o-mini) - Digite 'sair' para fechar")
    print("-" * 50)

    # --- CORREÇÃO: A LISTA MESSAGES É CRIADA AQUI ---
    messages = [
        {"role": "system", "content": """
        Você é o atendente virtual da 'DevBurger'.
        Seu tom é prestativo e eficiente.
        
        REGRAS:
        1. Use 'listar_cardapio' se o cliente perguntar preços ou opções.
        2. Não invente produtos. Use os dados do cardápio.
        3. Para fechar o pedido, você PRECISA OBRIGATORIAMENTE de: Nome, Telefone, Endereço e Itens.
        4. Antes de chamar 'finalizar_pedido', confirme o resumo e o endereço.
        5. Seja breve.
        """}
    ]
    # ------------------------------------------------

    while True:
        user_input = input("\nVocê: ")
        if user_input.lower() in ["sair", "exit"]:
            break

        # Adiciona mensagem do usuário ao histórico
        messages.append({"role": "user", "content": user_input})

        try:
            # --- CHAMADA À API ---
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools_schema,
                tool_choice="auto" 
            )

            msg_bot = response.choices[0].message

            # Se a IA decidiu chamar uma ferramenta...
            if msg_bot.tool_calls:
                # 1. Adiciona a intenção da IA no histórico
                messages.append(msg_bot)

                # 2. Processa cada ferramenta solicitada
                for tool_call in msg_bot.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    print(f"⚙️  [IA CHAMOU]: {func_name}")

                    # Executa a função Python real
                    funcao_python = funcoes_disponiveis.get(func_name)
                    
                    if func_name == "finalizar_pedido":
                        try:
                            itens_obj = [ItemPedidoInput(**item) for item in func_args['itens']]
                            resultado = funcao_python(
                                nome_cliente=func_args['nome_cliente'],
                                telefone=func_args['telefone'],
                                endereco=func_args['endereco'],
                                itens=itens_obj
                            )
                        except Exception as e:
                            resultado = f"Erro nos dados do pedido: {e}"
                    else:
                        resultado = funcao_python(**func_args)

                    print(f"📊 [RETORNO DB]: {str(resultado)[:100]}...")

                    # 3. Devolve a resposta da ferramenta para a IA
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": str(resultado)
                    })

                # 4. Chama a IA de novo para ela ler o resultado e responder o cliente
                final_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
                resposta_final = final_response.choices[0].message.content
                print(f"🤖 Bot: {resposta_final}")
                messages.append({"role": "assistant", "content": resposta_final})

            else:
                # Se não houve chamada de função, apenas imprime o texto
                print(f"🤖 Bot: {msg_bot.content}")
                messages.append(msg_bot)

        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    chat_loop()
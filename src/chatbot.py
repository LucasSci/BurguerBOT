import os
import json
from openai import OpenAI
from src.tools import listar_cardapio, finalizar_pedido, ItemPedidoInput

class BurgerBrain:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Melhoria futura: Trocar esse dicionário por Banco de Dados (Redis/Postgres)
        self.historico = {} 
        self.system_prompt = """
            Você é o atendente virtual da 'DevBurger'. 
            Seu tom é prestativo, informal e direto.
            REGRAS:
            1. Use 'listar_cardapio' para ver preços.
            2. Para 'finalizar_pedido', colete: Nome, Telefone, Endereço e Itens.
            3. Confirme o valor total antes de fechar.
            4. Se o usuário pedir algo fora do cardápio, diga gentilmente que não temos.
        """
        
        # Schema das ferramentas (igual estava no seu código)
        self.tools_schema = [
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

    def processar_mensagem(self, numero_cliente: str, mensagem_usuario: str) -> str:
        # 1. Inicia histórico se não existir
        if numero_cliente not in self.historico:
            self.historico[numero_cliente] = [{"role": "system", "content": self.system_prompt}]
        
        self.historico[numero_cliente].append({"role": "user", "content": mensagem_usuario})

        try:
            # 2. Primeira chamada a IA
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.historico[numero_cliente],
                tools=self.tools_schema,
                tool_choice="auto"
            )
            msg_bot = response.choices[0].message

            # 3. Verifica uso de ferramentas
            if msg_bot.tool_calls:
                self.historico[numero_cliente].append(msg_bot) # Adiciona a intenção da IA
                
                for tool in msg_bot.tool_calls:
                    func_name = tool.function.name
                    args = json.loads(tool.function.arguments)
                    
                    print(f"⚙️ [BRAIN] Executando ferramenta: {func_name}")
                    
                    if func_name == "listar_cardapio":
                        resultado = listar_cardapio()
                    
                    elif func_name == "finalizar_pedido":
                        try:
                            # Converte para o objeto Pydantic que sua função espera
                            itens_obj = [ItemPedidoInput(**i) for i in args['itens']]
                            resultado = finalizar_pedido(
                                nome_cliente=args['nome_cliente'],
                                telefone=args['telefone'],
                                endereco=args['endereco'],
                                itens=itens_obj
                            )
                        except Exception as e:
                            resultado = f"Erro ao processar dados do pedido: {e}"
                    else:
                        resultado = "Ferramenta desconhecida."

                    # Devolve resultado para a IA
                    self.historico[numero_cliente].append({
                        "tool_call_id": tool.id,
                        "role": "tool",
                        "name": func_name,
                        "content": str(resultado)
                    })

                # 4. Segunda chamada (Resposta Final com os dados)
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.historico[numero_cliente]
                )
                resposta_texto = final_response.choices[0].message.content
            
            else:
                resposta_texto = msg_bot.content

            # Adiciona resposta final ao histórico
            self.historico[numero_cliente].append({"role": "assistant", "content": resposta_texto})
            return resposta_texto

        except Exception as e:
            print(f"❌ Erro no Brain: {e}")
            return "Desculpe, tive um erro interno. Pode repetir?"
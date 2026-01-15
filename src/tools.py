from typing import List, Optional
from pydantic import BaseModel, Field
from src.database import SessionLocal
from src.models import Produto, Pedido, ItemPedido

# --- DEFINIÇÃO DOS DADOS (Pydantic) ---
# Isso resolve o erro "missing field"
class ItemPedidoInput(BaseModel):
    produto: str = Field(description="Nome exato do produto conforme cardápio")
    quantidade: int = Field(description="Quantidade desejada")
    obs: Optional[str] = Field(default=None, description="Observações (ex: sem cebola)")

# --- FERRAMENTAS ---

def listar_cardapio():
    """
    Consulta o banco de dados e retorna os produtos disponíveis e preços.
    """
    db = SessionLocal()
    produtos = db.query(Produto).all()
    db.close()
    
    if not produtos:
        return "O cardápio está vazio."
    
    texto = "🍔 CARDÁPIO 🍔\n"
    for p in produtos:
        texto += f"- {p.nome}: R$ {p.preco:.2f}\n"
    return texto
# ... (ItemPedidoInput e listar_cardapio continuam iguais) ...

# Adicionamos o argumento 'endereco' aqui
def finalizar_pedido(nome_cliente: str, telefone: str, endereco: str, itens: List[ItemPedidoInput]):
    """
    Registra o pedido final.
    """
    print(f"DEBUG: Cliente: {nome_cliente} | Endereço: {endereco}")
    
    db = SessionLocal()
    try:
        # Passamos o endereço para o Banco
        novo_pedido = Pedido(
            cliente_nome=nome_cliente, 
            cliente_telefone=telefone,
            endereco=endereco 
        )
        db.add(novo_pedido)
        db.commit()
        
        total = 0.0
        resumo = []

        for item in itens:
            prod_db = db.query(Produto).filter(Produto.nome == item.produto).first()
            
            if not prod_db:
                return f"Erro: Produto '{item.produto}' não encontrado."

            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_nome=prod_db.nome,
                quantidade=item.quantidade,
                observacao=item.obs or "",
                preco_unitario=prod_db.preco
            )
            db.add(novo_item)
            subtotal = prod_db.preco * item.quantidade
            total += subtotal
            resumo.append(f"{item.quantidade}x {prod_db.nome}")

        novo_pedido.total = total
        db.commit()
        
        # Adicionei o endereço na resposta de confirmação
        return (f"✅ Pedido #{novo_pedido.id} confirmado!\n"
                f"🏠 Entrega em: {endereco}\n"
                f"🍔 Itens: {', '.join(resumo)}\n"
                f"💰 Total: R$ {total:.2f}")
        
    except Exception as e:
        db.rollback()
        return f"Erro interno ao salvar: {str(e)}"
    finally:
        db.close()

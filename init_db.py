from src.database import criar_tabelas, SessionLocal
from src.models import Produto

def inicializar_banco():
    print("Criando tabelas...")
    criar_tabelas()
    
    db = SessionLocal()
    
    # Verifica se já tem produtos para não duplicar
    if db.query(Produto).count() > 0:
        print("Banco já populado!")
        return

    print("Populando cardápio...")
    cardapio_inicial = [
        Produto(nome="X-Python", descricao="Pão brioche, burger 180g, queijo cheddar, bacon em tiras e molho especial.", preco=28.90, categoria="Lanche"),
        Produto(nome="Smash Java", descricao="Pão australiano, dois burgers de 80g amassados na chapa, queijo prato.", preco=22.50, categoria="Lanche"),
        Produto(nome="C++ Crispy", descricao="Burger de frango empanado super crocante com alface americana e maionese.", preco=24.00, categoria="Lanche"),
        Produto(nome="Batata Array", descricao="Porção de batata frita rústica com alecrim.", preco=12.00, categoria="Acompanhamento"),
        Produto(nome="Coca-Cola Lata", descricao="350ml bem gelada.", preco=6.00, categoria="Bebida"),
        Produto(nome="Suco Natural", descricao="Laranja ou Limão 500ml.", preco=10.00, categoria="Bebida"),
    ]

    db.add_all(cardapio_inicial)
    db.commit()
    print("Sucesso! Cardápio cadastrado.")

if __name__ == "__main__":
    inicializar_banco()
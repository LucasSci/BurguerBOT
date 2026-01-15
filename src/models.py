from sqlalchemy import String, Float, ForeignKey, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

# Classe Base para todos os modelos
class Base(DeclarativeBase):
    pass

class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    descricao: Mapped[str] = mapped_column(String(200)) # Importante para a IA vender o peixe
    preco: Mapped[float] = mapped_column(Float)
    categoria: Mapped[str] = mapped_column(String(50)) # Lanche, Bebida, Sobremesa

    def __repr__(self):
        return f"<{self.nome} (R$ {self.preco})>"

class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_nome: Mapped[str] = mapped_column(String(100), nullable=True)
    cliente_telefone: Mapped[str] = mapped_column(String(20))
    
    # --- NOVA COLUNA AQUI ---
    endereco: Mapped[str] = mapped_column(String(200), nullable=False) # Agora é obrigatório
    # ------------------------

    status: Mapped[str] = mapped_column(String(20), default="recebido")
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.now)
    total: Mapped[float] = mapped_column(Float, default=0.0)

    itens: Mapped[List["ItemPedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_nome: Mapped[str] = mapped_column(String(100), nullable=True)
    cliente_telefone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="recebido") # recebido, preparando, entregue
    data_criacao: Mapped[datetime] = mapped_column(default=datetime.now)
    total: Mapped[float] = mapped_column(Float, default=0.0)

    # Relacionamento com itens
    itens: Mapped[List["ItemPedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_nome: Mapped[str] = mapped_column(String(100)) # Salvamos o nome caso o produto mude depois
    quantidade: Mapped[int] = mapped_column(Integer)
    observacao: Mapped[str] = mapped_column(String(200), nullable=True) # Ex: Sem cebola
    preco_unitario: Mapped[float] = mapped_column(Float) # Preço no momento da compra

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
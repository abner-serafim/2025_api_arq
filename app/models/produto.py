# ./app/models/produto.py
# Define o modelo SQLAlchemy para a tabela Produto.
# ATUALIZADO: Adicionado relacionamento explícito com PedidoProduto usando back_populates.

from app import db
from decimal import Decimal
from sqlalchemy.orm import relationship # Importa relationship

class Produto(db.Model):
    """
    Modelo SQLAlchemy para a tabela Produto.
    Utiliza nomes de coluna em minúsculo.
    """
    __tablename__ = 'produto'

    # --- Colunas da Tabela ---
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ean = db.Column(db.String(13), unique=True, nullable=True)

    # --- Relacionamentos ---
    # Define explicitamente o relacionamento Um-para-Muitos com PedidoProduto
    # Um produto pode estar associado a muitos itens de pedido.
    # 'back_populates' conecta este lado com o atributo 'produto' no modelo PedidoProduto.
    # 'lazy=True' é o padrão, carrega os pedidos apenas quando acessados.
    pedidos_associados = relationship(
        "PedidoProduto", # Aponta para a classe de associação
        back_populates="produto", # Linka com o atributo 'produto' em PedidoProduto
        lazy=True
    )

    # --- Métodos Úteis ---
    def __repr__(self):
        return f"<Produto {self.id}: {self.nome} (R$ {self.valor})>"

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'valor': float(self.valor) if self.valor is not None else None,
            'ean': self.ean
        }


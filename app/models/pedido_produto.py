# ./app/models/pedido_produto.py
# Define o modelo SQLAlchemy para a tabela associativa PedidoProduto como uma classe.
# ATUALIZADO: Campos de snapshot sem o sufixo '_momento'.

from app import db
from sqlalchemy.orm import relationship
from decimal import Decimal # Para type hinting

class PedidoProduto(db.Model):
    """
    Modelo SQLAlchemy para a tabela associativa PedidoProduto (Association Object).
    Inclui campos para armazenar um snapshot dos dados do produto.
    """
    __tablename__ = 'pedido_produto' # Nome da tabela

    # Chaves primárias compostas / estrangeiras
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), primary_key=True)

    # --- Campos de Snapshot do Produto (sem _momento) ---
    nome_produto = db.Column(db.String(255), nullable=False) # Era nome_produto_momento
    ean_produto = db.Column(db.String(13), nullable=True)   # Era ean_produto_momento
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False) # Era valor_unitario_momento

    # --- Outros Atributos ---
    quantidade = db.Column(db.Integer, nullable=False)

    # --- Relacionamentos ---
    # Define a relação de volta para Pedido e Produto
    # 'back_populates' é usado em ambos os lados para manter a relação bidirecional sincronizada.
    pedido = relationship("Pedido", back_populates="produtos_associados")
    produto = relationship("Produto", back_populates="pedidos_associados") # Ainda útil para referência

    def __repr__(self):
        # Usa o novo nome do campo
        return f"<PedidoProduto Pedido:{self.pedido_id} ProdNome:{self.nome_produto} Qtd:{self.quantidade}>"

    def to_dict(self):
        """Converte o objeto PedidoProduto para um dicionário."""
        return {
            'produto_id': self.produto_id, # ID do produto original
            # Inclui os dados do snapshot do produto (sem _momento)
            'nome_produto': self.nome_produto,
            'ean_produto': self.ean_produto,
            'valor_unitario': float(self.valor_unitario) if self.valor_unitario is not None else None,
            # Quantidade
            'quantidade': self.quantidade,
        }


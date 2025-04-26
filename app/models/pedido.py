# ./app/models/pedido.py
# Define o modelo SQLAlchemy para a tabela Pedido.

import datetime
from app import db
from sqlalchemy.orm import relationship
from decimal import Decimal

# Import Cliente para type hinting (opcional)
# from .cliente import Cliente # Não estritamente necessário aqui

class Pedido(db.Model):
    """
    Modelo SQLAlchemy para a tabela Pedido.
    Inclui campos para armazenar um snapshot dos dados do cliente.
    """
    __tablename__ = 'pedido'

    id = db.Column(db.Integer, primary_key=True)
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    nome_cliente = db.Column(db.String(255), nullable=False)
    cpf_cliente = db.Column(db.String(14), nullable=False)
    endereco_entrega = db.Column(db.String(500), nullable=True)
    telefone_contato = db.Column(db.String(20), nullable=True)
    email_pedido = db.Column(db.String(120), nullable=True)
    qtd_total = db.Column(db.Integer, default=0, nullable=False)
    valor_total = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)

    # --- Relacionamentos ---
    # Relacionamento com Cliente: Usa back_populates para ligar com 'pedidos' em Cliente
    # REMOVIDO: backref=db.backref('pedidos', lazy=True)
    cliente = relationship("Cliente", back_populates="pedidos")

    # Relacionamento com PedidoProduto (mantido)
    produtos_associados = relationship(
        "PedidoProduto",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Pedido {self.id} - Cliente: {self.nome_cliente} - Valor {self.valor_total}>"

    def calcular_e_atualizar_totais(self):
        """Calcula qtd_total e valor_total com base nos itens associados."""
        nova_qtd_total = 0
        novo_valor_total = Decimal('0.00')
        for item in self.produtos_associados:
            nova_qtd_total += item.quantidade
            novo_valor_total += item.quantidade * item.valor_unitario
        self.qtd_total = nova_qtd_total
        self.valor_total = novo_valor_total

    def to_dict(self, include_items=False, include_cliente_atual=False): # Adiciona flag
        """Converte o objeto Pedido para um dicionário serializável."""
        data = {
            'id': self.id,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'cliente_id': self.cliente_id,
            # Dados do snapshot
            'nome_cliente': self.nome_cliente,
            'cpf_cliente': self.cpf_cliente,
            'endereco_entrega': self.endereco_entrega,
            'telefone_contato': self.telefone_contato,
            'email_pedido': self.email_pedido,
            # Totais
            'qtd_total': self.qtd_total,
            'valor_total': float(self.valor_total) if self.valor_total is not None else None,
        }
        if include_items:
            data['itens'] = [item.to_dict() for item in self.produtos_associados]

        # Inclui dados atuais do cliente se solicitado e se o cliente foi carregado
        if include_cliente_atual and self.cliente:
            data['cliente_atual'] = self.cliente.to_dict()

        return data

# ./app/models/cliente.py
# Define o modelo SQLAlchemy para a tabela Cliente, usando nomes em minúsculo.

from app import db
from sqlalchemy.orm import relationship # Importa relationship

class Cliente(db.Model):
    """
    Modelo SQLAlchemy para a tabela Cliente.
    Utiliza nomes de coluna em minúsculo.
    """
    __tablename__ = 'cliente'

    # --- Colunas da Tabela ---
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(500), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)

    # --- Relacionamentos ---
    # Define explicitamente o relacionamento Um-para-Muitos com Pedido
    # Um cliente pode ter muitos pedidos.
    # 'back_populates' conecta este lado com o atributo 'cliente' no modelo Pedido.
    # 'lazy=True' é o padrão, carrega os pedidos apenas quando acessados.
    pedidos = relationship("Pedido", back_populates="cliente", lazy=True)

    # --- Métodos Úteis ---
    def __repr__(self):
        return f"<Cliente {self.id}: {self.nome} ({self.cpf})>"

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'email': self.email
            # Não incluir 'pedidos' aqui para evitar loops e sobrecarga,
            # a menos que seja especificamente necessário e tratado com cuidado.
        }


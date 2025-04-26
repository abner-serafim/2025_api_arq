# ./app/services/cliente_service.py
# Contém a lógica de negócio para Cliente, usando SQLAlchemy, nomes minúsculos e incluindo o campo email.

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import db
from app.models.cliente import Cliente

def _build_sqlalchemy_filters(query, filters):
    """Aplica filtros SQLAlchemy a uma query existente, usando nomes em minúsculo."""
    # Adiciona 'email' aos filtros permitidos
    allowed_filters = ['nome', 'cpf', 'telefone', 'endereco', 'email']

    for key, value in filters.items():
        if key in allowed_filters and value:
            model_attr = getattr(Cliente, key, None)
            if model_attr:
                # Usa ilike para nome/endereco/email
                if key in ['nome', 'endereco', 'email']:
                    query = query.filter(model_attr.ilike(f"%{value}%"))
                else: # Busca exata para cpf/telefone
                    query = query.filter(model_attr == value)
    return query

def get_all_clientes_service(filters=None):
    """Busca todos os clientes, aplicando filtros opcionais."""
    try:
        query = Cliente.query
        if filters:
            query = _build_sqlalchemy_filters(query, filters)
        clientes = query.all()
        # O to_dict() no modelo já inclui o email
        return [cliente.to_dict() for cliente in clientes], None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar clientes: {e}")
        return None, f"Erro de banco de dados ao buscar clientes: {e}"

def count_clientes_service(filters=None):
    """Conta o número total de clientes, aplicando filtros opcionais."""
    try:
        query = db.session.query(db.func.count(Cliente.id))
        if filters:
            count_query = Cliente.query
            count_query = _build_sqlalchemy_filters(count_query, filters)
            count = count_query.count()
        else:
            count = query.scalar()
        return count, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao contar clientes: {e}")
        return None, f"Erro de banco de dados ao contar clientes: {e}"

def get_cliente_by_id_service(cliente_id):
    """Busca um cliente específico pelo seu ID."""
    try:
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            return cliente.to_dict(), None # to_dict() inclui email
        else:
            return None, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar cliente por ID: {e}")
        return None, f"Erro de banco de dados ao buscar cliente por ID: {e}"

def create_cliente_service(cliente_data):
    """Cria um novo cliente, incluindo o campo opcional 'email'."""
    required_fields = ['nome', 'cpf']
    if not all(field in cliente_data and cliente_data[field] for field in required_fields):
        return None, "Erro: Campos obrigatórios ausentes ou vazios (nome, cpf)."

    # Cria instância incluindo o email (usa .get() pois é nullable)
    novo_cliente = Cliente(
        nome=cliente_data['nome'],
        cpf=cliente_data['cpf'],
        telefone=cliente_data.get('telefone'),
        endereco=cliente_data.get('endereco'),
        email=cliente_data.get('email') # Adiciona email
    )

    try:
        db.session.add(novo_cliente)
        db.session.commit()
        return novo_cliente.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao criar cliente: {e}")
        # Verifica qual constraint falhou (CPF ou Email)
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            if cliente_data.get('cpf') and f"'{cliente_data.get('cpf')}'" in str(e):
                return None, f"Erro: CPF '{cliente_data.get('cpf')}' já cadastrado."
            if cliente_data.get('email') and f"'{cliente_data.get('email')}'" in str(e):
                return None, f"Erro: Email '{cliente_data.get('email')}' já cadastrado."
            return None, "Erro: Violação de restrição de unicidade (CPF ou Email)." # Genérico se não conseguir identificar
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao criar cliente: {e}")
        return None, f"Erro de banco de dados ao criar cliente: {e}"

def update_cliente_service(cliente_id, cliente_data):
    """Atualiza todos os dados de um cliente (PUT), incluindo 'email'."""
    # Adiciona 'email' aos campos esperados para PUT (mesmo sendo nullable)
    required_fields = ['nome', 'cpf', 'telefone', 'endereco', 'email']
    if not all(field in cliente_data for field in required_fields):
        return None, "Erro: Para PUT, todos os campos devem ser enviados (nome, cpf, telefone, endereco, email)."

    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None, "Erro: Cliente não encontrado."

        # Atualiza todos os campos, incluindo email
        cliente.nome = cliente_data['nome']
        cliente.cpf = cliente_data['cpf']
        cliente.telefone = cliente_data.get('telefone')
        cliente.endereco = cliente_data.get('endereco')
        cliente.email = cliente_data.get('email') # Atualiza email

        db.session.commit()
        return cliente.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao atualizar cliente (PUT): {e}")
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            # Verifica qual campo duplicou
            if cliente_data.get('cpf') and f"'{cliente_data.get('cpf')}'" in str(e):
                return None, f"Erro: CPF '{cliente_data.get('cpf')}' já pertence a outro cliente."
            if cliente_data.get('email') and f"'{cliente_data.get('email')}'" in str(e):
                return None, f"Erro: Email '{cliente_data.get('email')}' já pertence a outro cliente."
            return None, "Erro: Violação de restrição de unicidade (CPF ou Email)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao atualizar cliente (PUT): {e}")
        return None, f"Erro de banco de dados ao atualizar cliente: {e}"

def patch_cliente_service(cliente_id, cliente_data):
    """Atualiza parcialmente um cliente (PATCH), permitindo atualizar 'email'."""
    if not cliente_data:
        return None, "Erro: Nenhum dado fornecido para atualização (PATCH)."

    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None, "Erro: Cliente não encontrado."

        updated = False
        # Adiciona 'email' aos campos permitidos para PATCH
        allowed_fields = ['nome', 'cpf', 'telefone', 'endereco', 'email']
        for key, value in cliente_data.items():
            if key in allowed_fields and hasattr(cliente, key):
                setattr(cliente, key, value)
                updated = True

        if not updated:
            return None, "Erro: Nenhum campo válido fornecido para atualização (PATCH)."

        db.session.commit()
        return cliente.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao atualizar cliente (PATCH): {e}")
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            # Verifica qual campo duplicou
            if 'cpf' in cliente_data and f"'{cliente_data.get('cpf')}'" in str(e):
                return None, f"Erro: CPF '{cliente_data.get('cpf')}' já pertence a outro cliente."
            if 'email' in cliente_data and f"'{cliente_data.get('email')}'" in str(e):
                return None, f"Erro: Email '{cliente_data.get('email')}' já pertence a outro cliente."
            return None, "Erro: Violação de restrição de unicidade (CPF ou Email)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao atualizar cliente (PATCH): {e}")
        return None, f"Erro de banco de dados ao atualizar cliente: {e}"

# A função delete_cliente_service não precisa de alterações diretas
# para suportar a coluna email, mas o tratamento de erro de integridade
# já cobre o caso de FKs.
def delete_cliente_service(cliente_id):
    """Deleta um cliente."""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None, "Erro: Cliente não encontrado."

        # Verificação de dependência (exemplo)
        # from app.models.pedido import Pedido
        # if Pedido.query.filter_by(cliente_id=cliente_id).first():
        #     return None, "Erro: Não é possível excluir cliente pois ele possui pedidos associados."

        db.session.delete(cliente)
        db.session.commit()
        return {"message": f"Cliente com ID {cliente_id} deletado com sucesso."}, None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao deletar cliente: {e}")
        if 'FOREIGN KEY constraint fails' in str(e):
            return None, "Erro: Não é possível excluir cliente pois ele possui registros dependentes (ex: pedidos)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao deletar cliente: {e}")
        return None, f"Erro de banco de dados ao deletar cliente: {e}"


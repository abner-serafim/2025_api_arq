# ./app/services/produto_service.py
# Contém a lógica de negócio para a entidade Produto, usando SQLAlchemy.

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func # Para usar funções como ilike
from decimal import Decimal, InvalidOperation # Para lidar com o tipo Numeric/Decimal
from app import db
from app.models.produto import Produto # Importa o modelo Produto

def _build_sqlalchemy_filters(query, filters):
    """Aplica filtros SQLAlchemy a uma query de Produto."""
    allowed_filters = ['nome', 'ean', 'valor_min', 'valor_max'] # Filtros permitidos

    for key, value in filters.items():
        if key in allowed_filters and value is not None: # Verifica se tem valor
            model_attr = getattr(Produto, key.split('_')[0], None) # Pega 'nome', 'ean', 'valor'

            if key == 'nome' and model_attr:
                query = query.filter(model_attr.ilike(f"%{value}%"))
            elif key == 'ean' and model_attr:
                query = query.filter(model_attr == value) # Busca exata para EAN
            elif key == 'valor_min' and model_attr:
                try:
                    valor_min_decimal = Decimal(value)
                    query = query.filter(Produto.valor >= valor_min_decimal)
                except InvalidOperation:
                    pass # Ignora filtro se o valor for inválido
            elif key == 'valor_max' and model_attr:
                try:
                    valor_max_decimal = Decimal(value)
                    query = query.filter(Produto.valor <= valor_max_decimal)
                except InvalidOperation:
                    pass # Ignora filtro se o valor for inválido
    return query

def get_all_produtos_service(filters=None):
    """Busca todos os produtos, aplicando filtros opcionais."""
    try:
        query = Produto.query
        if filters:
            query = _build_sqlalchemy_filters(query, filters)
        produtos = query.all()
        return [produto.to_dict() for produto in produtos], None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar produtos: {e}")
        return None, f"Erro de banco de dados ao buscar produtos: {e}"

def count_produtos_service(filters=None):
    """Conta o número total de produtos, aplicando filtros opcionais."""
    try:
        query = db.session.query(db.func.count(Produto.id))
        if filters:
            count_query = Produto.query
            count_query = _build_sqlalchemy_filters(count_query, filters)
            count = count_query.count()
        else:
            count = query.scalar()
        return count, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao contar produtos: {e}")
        return None, f"Erro de banco de dados ao contar produtos: {e}"

def get_produto_by_id_service(produto_id):
    """Busca um produto específico pelo seu ID."""
    try:
        produto = Produto.query.get(produto_id)
        if produto:
            return produto.to_dict(), None
        else:
            return None, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar produto por ID: {e}")
        return None, f"Erro de banco de dados ao buscar produto por ID: {e}"

def create_produto_service(produto_data):
    """Cria um novo produto."""
    required_fields = ['nome', 'valor']
    if not all(field in produto_data and produto_data[field] is not None for field in required_fields):
        return None, "Erro: Campos obrigatórios ausentes ou vazios (nome, valor)."

    try:
        # Converte valor para Decimal
        valor_decimal = Decimal(produto_data['valor'])
    except (InvalidOperation, TypeError):
        return None, "Erro: Valor inválido. Deve ser um número."

    novo_produto = Produto(
        nome=produto_data['nome'],
        valor=valor_decimal,
        ean=produto_data.get('ean') # EAN é opcional
    )

    try:
        db.session.add(novo_produto)
        db.session.commit()
        return novo_produto.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao criar produto: {e}")
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            # Verifica se foi o EAN (único campo unique além do ID)
            if produto_data.get('ean') and f"'{produto_data.get('ean')}'" in str(e):
                return None, f"Erro: EAN '{produto_data.get('ean')}' já cadastrado."
            return None, "Erro: Violação de restrição de unicidade (EAN)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao criar produto: {e}")
        return None, f"Erro de banco de dados ao criar produto: {e}"

def update_produto_service(produto_id, produto_data):
    """Atualiza todos os dados de um produto (PUT)."""
    required_fields = ['nome', 'valor', 'ean'] # Exige todos para PUT (ean pode ser None)
    if not all(field in produto_data for field in required_fields):
        return None, "Erro: Para PUT, todos os campos devem ser enviados (nome, valor, ean)."

    try:
        # Converte valor para Decimal
        valor_decimal = Decimal(produto_data['valor'])
    except (InvalidOperation, TypeError):
        return None, "Erro: Valor inválido. Deve ser um número."

    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return None, "Erro: Produto não encontrado."

        produto.nome = produto_data['nome']
        produto.valor = valor_decimal
        produto.ean = produto_data.get('ean')

        db.session.commit()
        return produto.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao atualizar produto (PUT): {e}")
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            if produto_data.get('ean') and f"'{produto_data.get('ean')}'" in str(e):
                return None, f"Erro: EAN '{produto_data.get('ean')}' já pertence a outro produto."
            return None, "Erro: Violação de restrição de unicidade (EAN)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao atualizar produto (PUT): {e}")
        return None, f"Erro de banco de dados ao atualizar produto: {e}"

def patch_produto_service(produto_id, produto_data):
    """Atualiza parcialmente um produto (PATCH)."""
    if not produto_data:
        return None, "Erro: Nenhum dado fornecido para atualização (PATCH)."

    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return None, "Erro: Produto não encontrado."

        updated = False
        allowed_fields = ['nome', 'valor', 'ean']
        for key, value in produto_data.items():
            if key in allowed_fields and hasattr(produto, key):
                if key == 'valor':
                    # Trata a conversão para Decimal no PATCH também
                    try:
                        setattr(produto, key, Decimal(value))
                    except (InvalidOperation, TypeError):
                        return None, f"Erro: Valor inválido para o campo '{key}'. Deve ser um número."
                else:
                    setattr(produto, key, value)
                updated = True

        if not updated:
            return None, "Erro: Nenhum campo válido fornecido para atualização (PATCH)."

        db.session.commit()
        return produto.to_dict(), None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao atualizar produto (PATCH): {e}")
        if 'UNIQUE constraint failed' in str(e) or 'Duplicate entry' in str(e):
            if 'ean' in produto_data and f"'{produto_data.get('ean')}'" in str(e):
                return None, f"Erro: EAN '{produto_data.get('ean')}' já pertence a outro produto."
            return None, "Erro: Violação de restrição de unicidade (EAN)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao atualizar produto (PATCH): {e}")
        return None, f"Erro de banco de dados ao atualizar produto: {e}"

def delete_produto_service(produto_id):
    """Deleta um produto."""
    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return None, "Erro: Produto não encontrado."

        # Adicionar verificação de dependência (ex: PedidoProduto) antes de deletar
        # from app.models.pedido import PedidoProduto # Exemplo
        # if PedidoProduto.query.filter_by(produto_id=produto_id).first():
        #     return None, "Erro: Não é possível excluir produto pois ele está associado a pedidos."

        db.session.delete(produto)
        db.session.commit()
        return {"message": f"Produto com ID {produto_id} deletado com sucesso."}, None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro de Integridade ao deletar produto: {e}")
        if 'FOREIGN KEY constraint fails' in str(e):
            return None, "Erro: Não é possível excluir produto pois ele possui registros dependentes (ex: itens de pedido)."
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao deletar produto: {e}")
        return None, f"Erro de banco de dados ao deletar produto: {e}"


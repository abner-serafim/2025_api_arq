# ./app/services/pedido_service.py
# Contém a lógica de negócio para a entidade Pedido, usando SQLAlchemy.

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload # Para otimizar carregamento de relacionamentos
from decimal import Decimal, InvalidOperation
from datetime import datetime

from app import db
from app.models.pedido import Pedido
from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.pedido_produto import PedidoProduto

# --- Funções Auxiliares ---

def _buscar_cliente_ou_erro(cliente_id):
    """Busca um cliente pelo ID ou retorna erro."""
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")
    return cliente

def _buscar_produto_ou_erro(produto_id):
    """Busca um produto pelo ID ou retorna erro."""
    produto = Produto.query.get(produto_id)
    if not produto:
        raise ValueError(f"Produto com ID {produto_id} não encontrado.")
    return produto

def _validar_item_pedido(item_data):
    """Valida os dados de um item do pedido."""
    if not isinstance(item_data, dict):
        raise ValueError("Formato inválido para item do pedido.")
    produto_id = item_data.get('produto_id')
    quantidade = item_data.get('quantidade')
    if not produto_id or not isinstance(produto_id, int):
        raise ValueError("ID do produto inválido ou ausente no item.")
    if not quantidade or not isinstance(quantidade, int) or quantidade <= 0:
        raise ValueError(f"Quantidade inválida ou ausente para o produto ID {produto_id}.")
    return produto_id, quantidade

# --- Serviços Principais ---

def create_pedido_service(pedido_data):
    """
    Cria um novo pedido com seus itens.
    'pedido_data' deve conter: cliente_id, endereco_entrega (opcional),
                                email_pedido (opcional), telefone_contato (opcional),
                                e uma lista 'itens' com {'produto_id': id, 'quantidade': qtd}.
    """
    cliente_id = pedido_data.get('cliente_id')
    itens_data = pedido_data.get('itens')

    if not cliente_id:
        return None, "Erro: ID do cliente é obrigatório."
    if not itens_data or not isinstance(itens_data, list) or not itens_data:
        return None, "Erro: Lista de itens do pedido está vazia ou inválida."

    try:
        # 1. Buscar Cliente e obter dados para snapshot
        cliente = _buscar_cliente_ou_erro(cliente_id)
        # Usa dados do cliente se não fornecido especificamente no pedido
        endereco_entrega = pedido_data.get('endereco_entrega', cliente.endereco)
        telefone_contato = pedido_data.get('telefone_contato', cliente.telefone)
        email_pedido = pedido_data.get('email_pedido', cliente.email)

        # 2. Criar o objeto Pedido (ainda sem totais)
        novo_pedido = Pedido(
            cliente_id=cliente.id,
            nome_cliente=cliente.nome, # Snapshot
            cpf_cliente=cliente.cpf,    # Snapshot
            endereco_entrega=endereco_entrega,
            telefone_contato=telefone_contato,
            email_pedido=email_pedido,
            qtd_total=0, # Será calculado
            valor_total=Decimal('0.00') # Será calculado
        )
        db.session.add(novo_pedido)
        # Flush para obter o ID do pedido antes de criar os itens, se necessário,
        # mas podemos adicionar os itens antes do commit final.
        # db.session.flush()

        # 3. Processar Itens e criar PedidoProduto
        itens_pedido_obj = []
        produtos_processados = set() # Para evitar duplicidade de produto no mesmo pedido inicial
        for item_data in itens_data:
            produto_id, quantidade = _validar_item_pedido(item_data)

            if produto_id in produtos_processados:
                raise ValueError(f"Produto ID {produto_id} listado mais de uma vez no pedido inicial.")
            produtos_processados.add(produto_id)

            produto = _buscar_produto_ou_erro(produto_id)

            item_pedido = PedidoProduto(
                pedido=novo_pedido, # Associa ao pedido criado
                produto=produto,   # Associa ao produto buscado
                quantidade=quantidade,
                # Snapshots do produto
                nome_produto=produto.nome,
                ean_produto=produto.ean,
                valor_unitario=produto.valor # Valor no momento da criação
            )
            itens_pedido_obj.append(item_pedido)
            # Adiciona diretamente à coleção do pedido (se configurado corretamente)
            # novo_pedido.produtos_associados.append(item_pedido) # SQLAlchemy cuida disso

        # Adiciona todos os itens à sessão
        db.session.add_all(itens_pedido_obj)

        # 4. Calcular Totais e atualizar Pedido
        # É importante fazer isso *depois* que os itens foram criados e associados
        # na sessão, mas *antes* do commit final.
        novo_pedido.calcular_e_atualizar_totais()

        # 5. Commit da Transação
        db.session.commit()

        # Retorna o pedido criado, incluindo os itens
        return novo_pedido.to_dict(include_items=True), None

    except ValueError as ve: # Captura erros de validação (cliente/produto não encontrado, item inválido)
        db.session.rollback()
        print(f"Erro de validação ao criar pedido: {ve}")
        return None, f"Erro de validação: {ve}"
    except IntegrityError as e: # Captura erros de integridade do DB
        db.session.rollback()
        print(f"Erro de Integridade ao criar pedido: {e}")
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e: # Captura outros erros do SQLAlchemy
        db.session.rollback()
        print(f"Erro SQLAlchemy ao criar pedido: {e}")
        return None, f"Erro de banco de dados ao criar pedido: {e}"

def get_all_pedidos_service(filters=None):
    """Busca todos os pedidos, aplicando filtros opcionais."""
    try:
        query = Pedido.query.order_by(Pedido.data_criacao.desc()) # Ordena pelos mais recentes

        if filters:
            cliente_id = filters.get('cliente_id')
            data_inicio = filters.get('data_inicio')
            data_fim = filters.get('data_fim')

            if cliente_id:
                try:
                    query = query.filter(Pedido.cliente_id == int(cliente_id))
                except ValueError:
                    pass # Ignora filtro se cliente_id inválido
            if data_inicio:
                try:
                    dt_inicio = datetime.fromisoformat(data_inicio)
                    query = query.filter(Pedido.data_criacao >= dt_inicio)
                except ValueError:
                    pass # Ignora filtro se data inválida
            if data_fim:
                try:
                    # Adiciona lógica para incluir o dia inteiro na data fim
                    dt_fim = datetime.fromisoformat(data_fim).replace(hour=23, minute=59, second=59, microsecond=999999)
                    query = query.filter(Pedido.data_criacao <= dt_fim)
                except ValueError:
                    pass # Ignora filtro se data inválida

        pedidos = query.all()
        # Não inclui itens por padrão na listagem geral para performance
        return [pedido.to_dict(include_items=False) for pedido in pedidos], None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar pedidos: {e}")
        return None, f"Erro de banco de dados ao buscar pedidos: {e}"

def count_pedidos_service(filters=None):
    """Conta o número total de pedidos, aplicando filtros opcionais."""
    try:
        # Query base para contagem
        query = db.session.query(db.func.count(Pedido.id))
        entity_query = Pedido.query # Query para aplicar filtros

        if filters:
            cliente_id = filters.get('cliente_id')
            data_inicio = filters.get('data_inicio')
            data_fim = filters.get('data_fim')

            if cliente_id:
                try:
                    entity_query = entity_query.filter(Pedido.cliente_id == int(cliente_id))
                except ValueError:
                    pass
            if data_inicio:
                try:
                    dt_inicio = datetime.fromisoformat(data_inicio)
                    entity_query = entity_query.filter(Pedido.data_criacao >= dt_inicio)
                except ValueError:
                    pass
            if data_fim:
                try:
                    dt_fim = datetime.fromisoformat(data_fim).replace(hour=23, minute=59, second=59, microsecond=999999)
                    entity_query = entity_query.filter(Pedido.data_criacao <= dt_fim)
                except ValueError:
                    pass

            # Conta sobre a query filtrada
            count = entity_query.count()
        else:
            # Conta todos
            count = query.scalar()

        return count, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao contar pedidos: {e}")
        return None, f"Erro de banco de dados ao contar pedidos: {e}"


def get_pedido_by_id_service(pedido_id, include_items=False):
    """Busca um pedido específico pelo seu ID, opcionalmente incluindo itens."""
    try:
        query = Pedido.query
        if include_items:
            # Eager loading dos itens associados para evitar múltiplas queries
            # selectinload é geralmente bom para coleções Um-para-Muitos/Muitos-para-Muitos
            query = query.options(selectinload(Pedido.produtos_associados))
            # Se precisar dos detalhes do produto também dentro do item:
            # query = query.options(selectinload(Pedido.produtos_associados).selectinload(PedidoProduto.produto))

        pedido = query.get(pedido_id)

        if pedido:
            return pedido.to_dict(include_items=include_items), None
        else:
            return None, None # Não encontrado
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao buscar pedido por ID: {e}")
        return None, f"Erro de banco de dados ao buscar pedido por ID: {e}"

# --- Serviços para Itens de Pedido (Adicionar/Atualizar/Remover) ---

def add_item_to_pedido_service(pedido_id, item_data):
    """Adiciona um novo item a um pedido existente."""
    try:
        # Valida os dados do item
        produto_id, quantidade = _validar_item_pedido(item_data)

        # Busca o pedido e o produto
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return None, f"Pedido com ID {pedido_id} não encontrado."
        produto = _buscar_produto_ou_erro(produto_id)

        # Verifica se o produto já existe neste pedido
        item_existente = PedidoProduto.query.filter_by(pedido_id=pedido_id, produto_id=produto_id).first()
        if item_existente:
            # Poderia atualizar a quantidade aqui ou retornar erro, dependendo da regra
            # return None, f"Produto ID {produto_id} já existe no pedido {pedido_id}. Use a rota de atualização de item."
            # Ou atualiza a quantidade:
            item_existente.quantidade += quantidade
            # Recalcula valor unitário? Não, deve manter o do momento da *primeira* adição, ou atualizar? Decisão de negócio.
            # Vamos manter o valor unitário original e apenas somar quantidade.
        else:
            # Cria o novo item
            novo_item = PedidoProduto(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                nome_produto=produto.nome,
                ean_produto=produto.ean,
                valor_unitario=produto.valor
            )
            db.session.add(novo_item)

        # Recalcula e atualiza os totais do pedido
        pedido.calcular_e_atualizar_totais()
        # Precisamos fazer commit para salvar o item e os totais atualizados
        db.session.commit()

        # Retorna o pedido atualizado com itens
        return get_pedido_by_id_service(pedido_id, include_items=True)

    except ValueError as ve:
        db.session.rollback()
        return None, f"Erro de validação: {ve}"
    except IntegrityError as e:
        db.session.rollback()
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Erro de banco de dados ao adicionar item: {e}"


def update_item_in_pedido_service(pedido_id, produto_id, item_data):
    """Atualiza um item (quantidade) em um pedido existente."""
    quantidade = item_data.get('quantidade')
    if not quantidade or not isinstance(quantidade, int) or quantidade <= 0:
        raise ValueError(f"Quantidade inválida ou ausente para atualização.")

    try:
        # Busca o item específico na tabela de associação
        item = PedidoProduto.query.filter_by(pedido_id=pedido_id, produto_id=produto_id).first()
        if not item:
            return None, f"Item com Produto ID {produto_id} não encontrado no Pedido ID {pedido_id}."

        # Atualiza a quantidade
        item.quantidade = quantidade
        # O valor unitário do momento não deve ser alterado aqui

        # Recalcula e atualiza os totais do pedido pai
        item.pedido.calcular_e_atualizar_totais()
        db.session.commit()

        # Retorna o pedido atualizado com itens
        return get_pedido_by_id_service(pedido_id, include_items=True)

    except ValueError as ve:
        db.session.rollback()
        return None, f"Erro de validação: {ve}"
    except IntegrityError as e:
        db.session.rollback()
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Erro de banco de dados ao atualizar item: {e}"


def remove_item_from_pedido_service(pedido_id, produto_id):
    """Remove um item de um pedido existente."""
    try:
        # Busca o item específico
        item = PedidoProduto.query.filter_by(pedido_id=pedido_id, produto_id=produto_id).first()
        if not item:
            return None, f"Item com Produto ID {produto_id} não encontrado no Pedido ID {pedido_id}."

        # Guarda referência ao pedido pai antes de deletar o item
        pedido_pai = item.pedido

        # Remove o item
        db.session.delete(item)
        # Não precisa fazer commit ainda, recalcular primeiro

        # Recalcula e atualiza os totais do pedido pai
        # É importante chamar isso *depois* que o item foi marcado para delete na sessão
        # mas *antes* do commit final. O SQLAlchemy é inteligente o suficiente.
        pedido_pai.calcular_e_atualizar_totais()
        db.session.commit()

        # Retorna o pedido atualizado com itens
        return get_pedido_by_id_service(pedido_id, include_items=True)

    except IntegrityError as e: # Pouco provável aqui, mas por segurança
        db.session.rollback()
        return None, f"Erro de integridade no banco de dados: {e}"
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Erro de banco de dados ao remover item: {e}"


# --- Serviços de Atualização/Exclusão de Pedido ---

def patch_pedido_service(pedido_id, pedido_data):
    """Atualiza parcialmente um pedido (ex: email, endereco_entrega)."""
    if not pedido_data:
        return None, "Erro: Nenhum dado fornecido para atualização (PATCH)."

    try:
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return None, "Erro: Pedido não encontrado."

        updated = False
        # Campos permitidos para PATCH no pedido principal (não os itens)
        allowed_fields = ['endereco_entrega', 'telefone_contato', 'email_pedido']
        for key, value in pedido_data.items():
            if key in allowed_fields and hasattr(pedido, key):
                setattr(pedido, key, value)
                updated = True

        if not updated:
            return None, "Erro: Nenhum campo válido fornecido para atualização (PATCH)."

        db.session.commit()
        # Retorna o pedido atualizado (sem itens por padrão no PATCH)
        return pedido.to_dict(include_items=False), None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao atualizar pedido (PATCH): {e}")
        return None, f"Erro de banco de dados ao atualizar pedido: {e}"


def delete_pedido_service(pedido_id):
    """Deleta um pedido e seus itens associados (devido ao cascade)."""
    try:
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return None, "Erro: Pedido não encontrado."

        db.session.delete(pedido)
        db.session.commit()
        return {"message": f"Pedido com ID {pedido_id} e seus itens foram deletados com sucesso."}, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Erro SQLAlchemy ao deletar pedido: {e}")
        return None, f"Erro de banco de dados ao deletar pedido: {e}"


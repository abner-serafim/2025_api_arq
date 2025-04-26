# ./app/controllers/pedido_controller.py
# Define os endpoints da API REST para a entidade Pedido.

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app import require_api_key
from app.services.pedido_service import (
    create_pedido_service,
    get_all_pedidos_service,
    count_pedidos_service,
    get_pedido_by_id_service,
    add_item_to_pedido_service,
    update_item_in_pedido_service,
    remove_item_from_pedido_service,
    patch_pedido_service,
    delete_pedido_service
)
# Importa schemas de outros controllers se necessário ou define aqui
# from .cliente_controller import ERROR_SCHEMA

# Define ERROR_SCHEMA aqui se não for importar
ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string", "description": "Mensagem de erro"}
    }
}


pedido_bp = Blueprint('pedido_bp', __name__)

# --- Definições de Schema para Swagger ---

PEDIDO_ITEM_INPUT_SCHEMA = {
    "type": "object",
    "required": ["produto_id", "quantidade"],
    "properties": {
        "produto_id": {"type": "integer", "description": "ID do produto a ser adicionado"},
        "quantidade": {"type": "integer", "description": "Quantidade do produto", "minimum": 1}
    }
}

PEDIDO_INPUT_SCHEMA = {
    "type": "object",
    "required": ["cliente_id", "itens"],
    "properties": {
        "cliente_id": {"type": "integer", "description": "ID do cliente que está fazendo o pedido"},
        "endereco_entrega": {"type": "string", "description": "Endereço de entrega (opcional, usa do cliente se omitido)"},
        "telefone_contato": {"type": "string", "description": "Telefone de contato para o pedido (opcional, usa do cliente se omitido)"},
        "email_pedido": {"type": "string", "format": "email", "description": "Email para o pedido (opcional, usa do cliente se omitido)"},
        "itens": {
            "type": "array",
            "description": "Lista de itens do pedido",
            "items": PEDIDO_ITEM_INPUT_SCHEMA,
            "minItems": 1
        }
    }
}

PEDIDO_ITEM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "produto_id": {"type": "integer"},
        "nome_produto": {"type": "string"},
        "ean_produto": {"type": "string", "nullable": True},
        "valor_unitario": {"type": "number", "format": "float"},
        "quantidade": {"type": "integer"}
    }
}

PEDIDO_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "data_criacao": {"type": "string", "format": "date-time"},
        "cliente_id": {"type": "integer"},
        "nome_cliente": {"type": "string"},
        "cpf_cliente": {"type": "string"},
        "endereco_entrega": {"type": "string", "nullable": True},
        "telefone_contato": {"type": "string", "nullable": True},
        "email_pedido": {"type": "string", "format": "email", "nullable": True},
        "qtd_total": {"type": "integer"},
        "valor_total": {"type": "number", "format": "float"},
        "itens": { # Opcional, incluído se solicitado
            "type": "array",
            "items": PEDIDO_ITEM_OUTPUT_SCHEMA
        }
    }
}

PEDIDO_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "endereco_entrega": {"type": "string", "description": "Novo endereço de entrega"},
        "telefone_contato": {"type": "string", "description": "Novo telefone de contato"},
        "email_pedido": {"type": "string", "format": "email", "description": "Novo email para o pedido"}
    },
    "minProperties": 1
}

ITEM_UPDATE_SCHEMA = {
    "type": "object",
    "required": ["quantidade"],
    "properties": {
        "quantidade": {"type": "integer", "description": "Nova quantidade do item", "minimum": 1}
    }
}


# --- Endpoints da API ---

@pedido_bp.route('', methods=['POST'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Cria um novo pedido',
    'description': 'Cria um pedido para um cliente com uma lista de produtos e quantidades.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [{'name': 'body', 'in': 'body', 'required': True, 'schema': PEDIDO_INPUT_SCHEMA}],
    'responses': {
        '201': {'description': 'Pedido criado com sucesso.', 'schema': PEDIDO_OUTPUT_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos, cliente/produto não encontrado, item duplicado, etc.).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno do servidor.', 'schema': ERROR_SCHEMA}
    }
})
def create_pedido():
    """ Rota POST /api/pedidos """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    pedido, error = create_pedido_service(data)

    if error:
        # Erros de validação ou de negócio são 400
        if "Erro de validação" in error or "não encontrado" in error or "inválido" in error or "duplicado" in error:
            return jsonify({"message": error}), 400
        # Outros erros (DB) são 500
        return jsonify({"message": error}), 500

    return jsonify(pedido), 201

@pedido_bp.route('', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Lista ou filtra pedidos',
    'description': 'Retorna uma lista de pedidos. Permite filtrar por cliente_id, data_inicio, data_fim.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'cliente_id', 'in': 'query', 'type': 'integer', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'description': 'Formato YYYY-MM-DD', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'description': 'Formato YYYY-MM-DD', 'required': False}
    ],
    'responses': {
        '200': {'description': 'Lista de pedidos.', 'schema': {'type': 'array', 'items': PEDIDO_OUTPUT_SCHEMA}}, # Schema sem itens por padrão
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_all_pedidos():
    """ Rota GET /api/pedidos """
    filters = {k: v for k, v in request.args.items() if v}
    pedidos, error = get_all_pedidos_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify(pedidos), 200

@pedido_bp.route('/count', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Conta pedidos',
    'description': 'Retorna a quantidade total de pedidos, com filtros opcionais.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'cliente_id', 'in': 'query', 'type': 'integer', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False}
    ],
    'responses': {
        '200': {'description': 'Contagem retornada.', 'schema': {'type': 'object', 'properties': {'total_pedidos': {'type': 'integer'}}}},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def count_pedidos():
    """ Rota GET /api/pedidos/count """
    filters = {k: v for k, v in request.args.items() if v}
    count, error = count_pedidos_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify({"total_pedidos": count}), 200

@pedido_bp.route('/<int:pedido_id>', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Busca pedido por ID',
    'description': 'Retorna os detalhes de um pedido específico. Use ?include_items=true para ver os produtos.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'include_items', 'in': 'query', 'type': 'boolean', 'required': False, 'default': False}
    ],
    'responses': {
        '200': {'description': 'Pedido encontrado.', 'schema': PEDIDO_OUTPUT_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_pedido(pedido_id):
    """ Rota GET /api/pedidos/{id} """
    include_items_param = request.args.get('include_items', 'false').lower() == 'true'
    pedido, error = get_pedido_by_id_service(pedido_id, include_items=include_items_param)
    if error:
        return jsonify({"message": error}), 500
    if not pedido:
        return jsonify({"message": "Erro: Pedido não encontrado."}), 404
    return jsonify(pedido), 200

@pedido_bp.route('/<int:pedido_id>', methods=['PATCH'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Atualiza parcialmente um pedido',
    'description': 'Atualiza campos como endereco_entrega, telefone_contato, email_pedido.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': PEDIDO_PATCH_SCHEMA}
    ],
    'responses': {
        '200': {'description': 'Pedido atualizado.', 'schema': PEDIDO_OUTPUT_SCHEMA}, # Retorna sem itens por padrão
        '400': {'description': 'Erro na requisição (nenhum dado válido).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def patch_pedido(pedido_id):
    """ Rota PATCH /api/pedidos/{id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    pedido, error = patch_pedido_service(pedido_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Nenhum dado" in error or "Nenhum campo válido" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not pedido:
        return jsonify({"message": "Erro: Pedido não encontrado."}), 404
    return jsonify(pedido), 200

@pedido_bp.route('/<int:pedido_id>', methods=['DELETE'])
@require_api_key
@swag_from({
    'tags': ['Pedidos'],
    'summary': 'Deleta um pedido',
    'description': 'Deleta um pedido e todos os seus itens associados.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [{'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        '200': {'description': 'Pedido deletado.', 'schema': {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def delete_pedido(pedido_id):
    """ Rota DELETE /api/pedidos/{id} """
    result, error = delete_pedido_service(pedido_id)
    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        return jsonify({"message": error}), 500
    if not result:
        return jsonify({"message": "Erro: Pedido não encontrado."}), 404
    return jsonify(result), 200

# --- Endpoints para Gerenciar Itens de um Pedido ---

@pedido_bp.route('/<int:pedido_id>/items', methods=['POST'])
@require_api_key
@swag_from({
    'tags': ['Pedidos Itens'],
    'summary': 'Adiciona um item a um pedido existente',
    'description': 'Adiciona um produto com quantidade a um pedido. Se o produto já existir, pode somar a quantidade (verificar lógica no serviço).',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': PEDIDO_ITEM_INPUT_SCHEMA}
    ],
    'responses': {
        '200': {'description': 'Item adicionado/atualizado, retorna pedido completo com itens.', 'schema': PEDIDO_OUTPUT_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos, produto já existe - dependendo da regra).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido ou Produto não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def add_item_to_pedido(pedido_id):
    """ Rota POST /api/pedidos/{id}/items """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    pedido_atualizado, error = add_item_to_pedido_service(pedido_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Erro de validação" in error or "inválido" in error or "já existe" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    return jsonify(pedido_atualizado), 200


@pedido_bp.route('/<int:pedido_id>/items/<int:produto_id>', methods=['PUT'])
@require_api_key
@swag_from({
    'tags': ['Pedidos Itens'],
    'summary': 'Atualiza a quantidade de um item em um pedido',
    'description': 'Modifica a quantidade de um produto específico dentro de um pedido.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': ITEM_UPDATE_SCHEMA} # Schema só com quantidade
    ],
    'responses': {
        '200': {'description': 'Quantidade do item atualizada, retorna pedido completo com itens.', 'schema': PEDIDO_OUTPUT_SCHEMA},
        '400': {'description': 'Erro na requisição (quantidade inválida).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido ou Item não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def update_item_in_pedido(pedido_id, produto_id):
    """ Rota PUT /api/pedidos/{id}/items/{produto_id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    pedido_atualizado, error = update_item_in_pedido_service(pedido_id, produto_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Erro de validação" in error or "inválida" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    return jsonify(pedido_atualizado), 200


@pedido_bp.route('/<int:pedido_id>/items/<int:produto_id>', methods=['DELETE'])
@require_api_key
@swag_from({
    'tags': ['Pedidos Itens'],
    'summary': 'Remove um item de um pedido',
    'description': 'Exclui um produto específico de um pedido.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'pedido_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        '200': {'description': 'Item removido, retorna pedido completo com itens.', 'schema': PEDIDO_OUTPUT_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Pedido ou Item não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def remove_item_from_pedido(pedido_id, produto_id):
    """ Rota DELETE /api/pedidos/{id}/items/{produto_id} """
    pedido_atualizado, error = remove_item_from_pedido_service(pedido_id, produto_id)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        return jsonify({"message": error}), 500
    return jsonify(pedido_atualizado), 200


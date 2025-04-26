# ./app/controllers/produto_controller.py
# Define os endpoints da API REST para a entidade Produto.

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app import require_api_key # Importa o decorator de autenticação
from app.services.produto_service import ( # Importa os serviços de produto
    get_all_produtos_service,
    count_produtos_service,
    get_produto_by_id_service,
    create_produto_service,
    update_produto_service,
    patch_produto_service,
    delete_produto_service
)

# Cria o Blueprint para produtos
produto_bp = Blueprint('produto_bp', __name__)

# --- Definições de Schema para Swagger ---

PRODUTO_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "ID único do produto"},
        "nome": {"type": "string", "description": "Nome do produto", "example": "Laptop XPTO"},
        # CORREÇÃO: Tipo number, formato float/double para valor
        "valor": {"type": "number", "format": "float", "description": "Preço do produto", "example": 4500.99},
        "ean": {"type": "string", "description": "Código EAN (código de barras)", "nullable": True, "example": "7891234567890"}
    }
}

PRODUTO_INPUT_SCHEMA = {
    "type": "object",
    "required": ["nome", "valor"],
    "properties": {
        "nome": {"type": "string", "description": "Nome do produto", "example": "Teclado Gamer"},
        # Input ainda pode ser string, a validação/conversão ocorre no serviço
        "valor": {"type": "string", "description": "Preço do produto (enviar como string, ex: \"199.90\")", "example": "199.90"},
        "ean": {"type": "string", "description": "Código EAN (opcional, único)", "example": "7890000111222"}
    }
}

PRODUTO_PUT_SCHEMA = {
    "type": "object",
    "required": ["nome", "valor", "ean"], # Exige todos para PUT (ean pode ser null)
    "properties": {
        "nome": {"type": "string", "description": "Nome do produto"},
        # Input ainda pode ser string
        "valor": {"type": "string", "description": "Preço do produto (enviar como string)"},
        "ean": {"type": "string", "description": "Código EAN (único)", "nullable": True}
    }
}

PRODUTO_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "nome": {"type": "string", "description": "Novo nome"},
        # Input ainda pode ser string
        "valor": {"type": "string", "description": "Novo preço (enviar como string)"},
        "ean": {"type": "string", "description": "Novo código EAN (único)", "nullable": True}
    },
    "minProperties": 1
}

ERROR_SCHEMA = { # Reutilizado do cliente_controller
    "type": "object",
    "properties": {
        "message": {"type": "string", "description": "Mensagem de erro"}
    }
}


# --- Endpoints da API ---

@produto_bp.route('', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Lista ou filtra produtos',
    'description': 'Retorna lista de produtos. Filtra por nome (parcial), ean (exato), valor_min, valor_max.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'nome', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'ean', 'in': 'query', 'type': 'string', 'required': False},
        # Mantém number para filtros de valor no Swagger
        {'name': 'valor_min', 'in': 'query', 'type': 'number', 'format': 'float', 'required': False},
        {'name': 'valor_max', 'in': 'query', 'type': 'number', 'format': 'float', 'required': False}
    ],
    'responses': {
        # CORREÇÃO: Schema de resposta usa o PRODUTO_SCHEMA atualizado
        '200': {'description': 'Lista de produtos.', 'schema': {'type': 'array', 'items': PRODUTO_SCHEMA}},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_all_produtos():
    """ Rota GET /api/produtos """
    filters = {k: v for k, v in request.args.items() if v is not None} # Pega args com valor
    produtos, error = get_all_produtos_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify(produtos), 200 # O jsonify do Flask lida bem com floats

@produto_bp.route('/count', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Conta produtos',
    'description': 'Retorna quantidade total de produtos, com filtros opcionais.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'nome', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'ean', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'valor_min', 'in': 'query', 'type': 'number', 'format': 'float', 'required': False},
        {'name': 'valor_max', 'in': 'query', 'type': 'number', 'format': 'float', 'required': False}
    ],
    'responses': {
        '200': {'description': 'Contagem retornada.', 'schema': {'type': 'object', 'properties': {'total_produtos': {'type': 'integer'}}}},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def count_produtos():
    """ Rota GET /api/produtos/count """
    filters = {k: v for k, v in request.args.items() if v is not None}
    count, error = count_produtos_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify({"total_produtos": count}), 200

@produto_bp.route('/<int:produto_id>', methods=['GET'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Busca produto por ID',
    'description': 'Retorna os detalhes de um produto específico.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [{'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        # CORREÇÃO: Schema de resposta usa o PRODUTO_SCHEMA atualizado
        '200': {'description': 'Produto encontrado.', 'schema': PRODUTO_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Produto não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_produto(produto_id):
    """ Rota GET /api/produtos/{id} """
    produto, error = get_produto_by_id_service(produto_id)
    if error:
        return jsonify({"message": error}), 500
    if not produto:
        return jsonify({"message": "Erro: Produto não encontrado."}), 404
    return jsonify(produto), 200

@produto_bp.route('', methods=['POST'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Cria novo produto',
    'description': 'Adiciona um novo produto ao banco de dados.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [{'name': 'body', 'in': 'body', 'required': True, 'schema': PRODUTO_INPUT_SCHEMA}],
    'responses': {
        # CORREÇÃO: Schema de resposta usa o PRODUTO_SCHEMA atualizado
        '201': {'description': 'Produto criado.', 'schema': PRODUTO_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos/faltando, EAN duplicado, valor inválido).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def create_produto():
    """ Rota POST /api/produtos """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    produto, error = create_produto_service(data)

    if error:
        if "obrigatórios" in error or "EAN" in error or "Valor inválido" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    return jsonify(produto), 201

@produto_bp.route('/<int:produto_id>', methods=['PUT'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Atualiza produto (substituição completa)',
    'description': 'Atualiza todos os dados de um produto existente.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': PRODUTO_PUT_SCHEMA}
    ],
    'responses': {
        # CORREÇÃO: Schema de resposta usa o PRODUTO_SCHEMA atualizado
        '200': {'description': 'Produto atualizado.', 'schema': PRODUTO_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos/faltando, EAN duplicado, valor inválido).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Produto não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def update_produto(produto_id):
    """ Rota PUT /api/produtos/{id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    produto, error = update_produto_service(produto_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "devem ser enviados" in error or "EAN" in error or "Valor inválido" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not produto:
        return jsonify({"message": "Erro: Produto não encontrado."}), 404
    return jsonify(produto), 200

@produto_bp.route('/<int:produto_id>', methods=['PATCH'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Atualiza parcialmente produto',
    'description': 'Atualiza um ou mais campos de um produto existente.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [
        {'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': PRODUTO_PATCH_SCHEMA}
    ],
    'responses': {
        # CORREÇÃO: Schema de resposta usa o PRODUTO_SCHEMA atualizado
        '200': {'description': 'Produto atualizado.', 'schema': PRODUTO_SCHEMA},
        '400': {'description': 'Erro na requisição (nenhum dado válido, EAN duplicado, valor inválido).', 'schema': ERROR_SCHEMA},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Produto não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def patch_produto(produto_id):
    """ Rota PATCH /api/produtos/{id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    produto, error = patch_produto_service(produto_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Nenhum dado" in error or "Nenhum campo válido" in error or "EAN" in error or "Valor inválido" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not produto:
        return jsonify({"message": "Erro: Produto não encontrado."}), 404
    return jsonify(produto), 200

@produto_bp.route('/<int:produto_id>', methods=['DELETE'])
@require_api_key
@swag_from({
    'tags': ['Produtos'],
    'summary': 'Deleta produto por ID',
    'description': 'Remove um produto do banco de dados.',
    'security': [{"ApiKeyAuth": []}],
    'parameters': [{'name': 'produto_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        '200': {'description': 'Produto deletado.', 'schema': {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        '401': {'description': 'Erro: Chave de API inválida ou ausente.', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Produto não encontrado.', 'schema': ERROR_SCHEMA},
        '400': {'description': 'Erro ao deletar (dependências).', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def delete_produto(produto_id):
    """ Rota DELETE /api/produtos/{id} """
    result, error = delete_produto_service(produto_id)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Não é possível excluir" in error or "registros dependentes" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not result:
        return jsonify({"message": "Erro: Produto não encontrado."}), 404
    return jsonify(result), 200

# ./app/controllers/cliente_controller.py
# Define os endpoints da API REST para Cliente, incluindo o campo email.

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.services.cliente_service import (
    get_all_clientes_service,
    count_clientes_service,
    get_cliente_by_id_service,
    create_cliente_service,
    update_cliente_service,
    patch_cliente_service,
    delete_cliente_service
)

cliente_bp = Blueprint('cliente_bp', __name__)

# --- Definições de Schema para Swagger (atualizadas com 'email') ---

CLIENTE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "ID único do cliente"},
        "nome": {"type": "string", "description": "Nome do cliente"},
        "cpf": {"type": "string", "description": "CPF do cliente"},
        "telefone": {"type": "string", "description": "Telefone de contato", "nullable": True},
        "endereco": {"type": "string", "description": "Endereço completo", "nullable": True},
        "email": {"type": "string", "format": "email", "description": "Endereço de email", "nullable": True, "example": "cliente@exemplo.com"} # Adiciona email
    }
}

CLIENTE_INPUT_SCHEMA = {
    "type": "object",
    "required": ["nome", "cpf"],
    "properties": {
        "nome": {"type": "string", "description": "Nome do cliente"},
        "cpf": {"type": "string", "description": "CPF do cliente"},
        "telefone": {"type": "string", "description": "Telefone (opcional)"},
        "endereco": {"type": "string", "description": "Endereço (opcional)"},
        "email": {"type": "string", "format": "email", "description": "Email (opcional, único)", "example": "novo@exemplo.com"} # Adiciona email
    }
}

CLIENTE_PUT_SCHEMA = {
    "type": "object",
    "required": ["nome", "cpf", "telefone", "endereco", "email"], # Exige email para PUT
    "properties": {
        "nome": {"type": "string", "description": "Nome do cliente"},
        "cpf": {"type": "string", "description": "CPF do cliente"},
        "telefone": {"type": "string", "description": "Telefone", "nullable": True},
        "endereco": {"type": "string", "description": "Endereço", "nullable": True},
        "email": {"type": "string", "format": "email", "description": "Email (único)", "nullable": True, "example": "atualizado@exemplo.com"} # Adiciona email
    }
}

CLIENTE_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "nome": {"type": "string", "description": "Novo nome"},
        "cpf": {"type": "string", "description": "Novo CPF"},
        "telefone": {"type": "string", "description": "Novo telefone"},
        "endereco": {"type": "string", "description": "Novo endereço"},
        "email": {"type": "string", "format": "email", "description": "Novo email (único)", "example": "patch@exemplo.com"} # Adiciona email
    },
    "minProperties": 1
}

ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string", "description": "Mensagem de erro"}
    }
}

# --- Endpoints da API ---

@cliente_bp.route('', methods=['GET'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Lista ou filtra clientes',
    'description': 'Retorna lista de clientes. Filtra por nome, cpf, telefone, endereco, email.',
    'parameters': [
        {'name': 'nome', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'cpf', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'telefone', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'endereco', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'email', 'in': 'query', 'type': 'string', 'required': False} # Adiciona filtro email
    ],
    'responses': {
        '200': {'description': 'Lista de clientes.', 'schema': {'type': 'array', 'items': CLIENTE_SCHEMA}},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_all_clientes():
    """ Rota GET /api/clientes """
    filters = {k: v for k, v in request.args.items() if v}
    clientes, error = get_all_clientes_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify(clientes), 200

@cliente_bp.route('/count', methods=['GET'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Conta clientes',
    'description': 'Retorna quantidade total de clientes, com filtros opcionais.',
    'parameters': [
        {'name': 'nome', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'cpf', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'email', 'in': 'query', 'type': 'string', 'required': False} # Adiciona filtro email
        # Adicionar outros filtros se necessário
    ],
    'responses': {
        '200': {'description': 'Contagem retornada.', 'schema': {'type': 'object', 'properties': {'total_clientes': {'type': 'integer'}}}},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def count_clientes():
    """ Rota GET /api/clientes/count """
    filters = {k: v for k, v in request.args.items() if v}
    count, error = count_clientes_service(filters)
    if error:
        return jsonify({"message": error}), 500
    return jsonify({"total_clientes": count}), 200

@cliente_bp.route('/<int:cliente_id>', methods=['GET'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Busca cliente por ID',
    'parameters': [{'name': 'cliente_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        '200': {'description': 'Cliente encontrado.', 'schema': CLIENTE_SCHEMA}, # Schema já inclui email
        '404': {'description': 'Cliente não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def get_cliente(cliente_id):
    """ Rota GET /api/clientes/{id} """
    cliente, error = get_cliente_by_id_service(cliente_id)
    if error:
        return jsonify({"message": error}), 500
    if not cliente:
        return jsonify({"message": "Erro: Cliente não encontrado."}), 404
    return jsonify(cliente), 200

@cliente_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Cria novo cliente',
    'parameters': [{'name': 'body', 'in': 'body', 'required': True, 'schema': CLIENTE_INPUT_SCHEMA}], # Schema já inclui email
    'responses': {
        '201': {'description': 'Cliente criado.', 'schema': CLIENTE_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos/faltando, CPF/Email duplicado).', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def create_cliente():
    """ Rota POST /api/clientes """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    cliente, error = create_cliente_service(data)

    if error:
        # Erros de validação ou duplicação (CPF/Email) são 400
        if "obrigatórios" in error or "CPF" in error or "Email" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    return jsonify(cliente), 201

@cliente_bp.route('/<int:cliente_id>', methods=['PUT'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Atualiza cliente (substituição completa)',
    'parameters': [
        {'name': 'cliente_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': CLIENTE_PUT_SCHEMA} # Schema atualizado
    ],
    'responses': {
        '200': {'description': 'Cliente atualizado.', 'schema': CLIENTE_SCHEMA},
        '400': {'description': 'Erro na requisição (dados inválidos/faltando, CPF/Email duplicado).', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Cliente não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def update_cliente(cliente_id):
    """ Rota PUT /api/clientes/{id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    cliente, error = update_cliente_service(cliente_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        # Erros de validação ou duplicação (CPF/Email) são 400
        if "devem ser enviados" in error or "CPF" in error or "Email" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not cliente:
        return jsonify({"message": "Erro: Cliente não encontrado."}), 404
    return jsonify(cliente), 200

@cliente_bp.route('/<int:cliente_id>', methods=['PATCH'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Atualiza parcialmente cliente',
    'parameters': [
        {'name': 'cliente_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': CLIENTE_PATCH_SCHEMA} # Schema atualizado
    ],
    'responses': {
        '200': {'description': 'Cliente atualizado.', 'schema': CLIENTE_SCHEMA},
        '400': {'description': 'Erro na requisição (nenhum dado válido, CPF/Email duplicado).', 'schema': ERROR_SCHEMA},
        '404': {'description': 'Cliente não encontrado.', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def patch_cliente(cliente_id):
    """ Rota PATCH /api/clientes/{id} """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Erro: Corpo da requisição JSON inválido ou vazio."}), 400

    cliente, error = patch_cliente_service(cliente_id, data)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        # Erros de validação ou duplicação (CPF/Email) são 400
        if "Nenhum dado" in error or "Nenhum campo válido" in error or "CPF" in error or "Email" in error or "unicidade" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not cliente:
        return jsonify({"message": "Erro: Cliente não encontrado."}), 404
    return jsonify(cliente), 200

# Rota DELETE não precisa de alteração no schema ou lógica principal
@cliente_bp.route('/<int:cliente_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Deleta cliente por ID',
    'parameters': [{'name': 'cliente_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        '200': {'description': 'Cliente deletado.', 'schema': {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        '404': {'description': 'Cliente não encontrado.', 'schema': ERROR_SCHEMA},
        '400': {'description': 'Erro ao deletar (dependências).', 'schema': ERROR_SCHEMA},
        '500': {'description': 'Erro interno.', 'schema': ERROR_SCHEMA}
    }
})
def delete_cliente(cliente_id):
    """ Rota DELETE /api/clientes/{id} """
    result, error = delete_cliente_service(cliente_id)

    if error:
        if "não encontrado" in error:
            return jsonify({"message": error}), 404
        if "Não é possível excluir" in error or "registros dependentes" in error:
            return jsonify({"message": error}), 400
        return jsonify({"message": error}), 500
    if not result:
        return jsonify({"message": "Erro: Cliente não encontrado."}), 404
    return jsonify(result), 200

# ./app/__init__.py
# Fábrica da aplicação Flask: configura a instância da app, extensões e blueprints.
# ADICIONADO: Configuração do Flask-CORS.

import os
from functools import wraps
from flask import Flask, request, jsonify
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS # Importa a extensão CORS

# --- Inicialização das Extensões ---
db = SQLAlchemy()
migrate = Migrate()
# Instância do CORS (ainda não vinculada à app)
# cors = CORS() # Pode inicializar aqui ou diretamente com a app

# Variável global para armazenar a chave de API esperada
EXPECTED_API_KEY = os.environ.get("API_KEY")

# --- Configuração do Swagger (sem alterações) ---
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}
template = {
    "swagger": "2.0",
    "info": {
        "title": "API de Clientes, Produtos e Pedidos (SQLAlchemy + CORS)",
        "description": "API REST para gerenciar dados de clientes, produtos e pedidos para parceiros, usando SQLAlchemy e com CORS habilitado.",
        "version": "1.0.3", # Incremento de versão
        "contact": {
            "email": "desenvolvedor@exemplo.com",
        },
    },
    "host": os.environ.get("FLASK_RUN_HOST", "localhost") + ":" + os.environ.get("FLASK_RUN_PORT", "5000"),
    "basePath": "/api",
    "schemes": [
        "http",
        # "https"
    ],
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-KEY",
            "in": "header",
            "description": "Chave de API para autenticação."
        }
    },
}
swagger = Swagger(template=template, config=swagger_config)


# --- Autenticação por Chave de API (Decorator - sem alterações) ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key or api_key != EXPECTED_API_KEY:
            print(f"Tentativa de acesso não autorizado com chave: {api_key}")
            return jsonify({"message": "Erro: Chave de API inválida ou ausente."}), 401, {'WWW-Authenticate': 'ApiKey realm="API Key Required"'}
        return f(*args, **kwargs)
    return decorated_function

# --- Fábrica da Aplicação ---
def create_app():
    app = Flask(__name__)

    # --- Configuração do Banco de Dados com SQLAlchemy (sem alterações) ---
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT", 3306)
    db_name = os.environ.get("DB_DATABASE")
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.environ.get('FLASK_DEBUG') == '1'

    # --- Inicializa as Extensões com a App ---
    db.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)

    # --- Inicializa o CORS ---
    # Permite requisições de qualquer origem para todas as rotas da API que começam com /api/
    # Em produção, substitua "*" pela lista de origens permitidas (ex: ['[http://parceiro1.com](http://parceiro1.com)', '[https://parceiro2.com](https://parceiro2.com)'])
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # Opções mais detalhadas:
    # CORS(app, resources={r"/api/*": {
    #     "origins": ["http://localhost:3000", "[https://meufrontend.com](https://meufrontend.com)"], # Lista de origens permitidas
    #     "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], # Métodos permitidos
    #     "allow_headers": ["Content-Type", "X-API-KEY", "Authorization"] # Cabeçalhos permitidos
    # }})


    # --- Importa os Models (sem alterações) ---
    from .models import cliente, produto, pedido, pedido_produto # noqa

    # --- Registro dos Blueprints (sem alterações) ---
    from .controllers.cliente_controller import cliente_bp
    from .controllers.produto_controller import produto_bp
    from .controllers.pedido_controller import pedido_bp

    app.register_blueprint(cliente_bp, url_prefix='/api/clientes')
    app.register_blueprint(produto_bp, url_prefix='/api/produtos')
    app.register_blueprint(pedido_bp, url_prefix='/api/pedidos')

    # --- Rotas de Verificação (sem alterações) ---
    @app.route('/')
    def index():
        return "Bem-vindo à API (SQLAlchemy + CORS)! Acesse /apidocs para a documentação Swagger."

    return app

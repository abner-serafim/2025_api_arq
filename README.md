# API REST de Clientes, Produtos e Pedidos

Esta é uma API REST desenvolvida em Python com Flask e SQLAlchemy para gerenciar dados de clientes, produtos e pedidos, destinada a ser consumida por parceiros. A aplicação segue o padrão MVC (adaptado para APIs) e utiliza Docker para facilitar a execução do ambiente completo (API, Banco de Dados MySQL, PhpMyAdmin).

## Para testar

* Acessar 'https://2025apiapk.abnerserafim.com.br/apidocs/'
* chave API_KEY 'minha-chave-secreta-123'

## Funcionalidades

* **Clientes:** CRUD completo (GET, GET por ID, POST, PUT, PATCH, DELETE), contagem e filtros.
* **Produtos:** CRUD completo, contagem e filtros (incluindo faixa de valor).
* **Pedidos:**
    * Criação de pedidos com múltiplos itens.
    * Consulta de pedidos (com filtros por cliente e data).
    * Consulta de pedido por ID (com opção de incluir itens e dados atuais do cliente).
    * Contagem de pedidos (com filtros).
    * Adição, atualização (quantidade) e remoção de itens de um pedido existente.
    * Atualização parcial de dados do pedido (endereço, telefone, email).
    * Exclusão de pedidos.
    * Armazenamento de *snapshot* dos dados do cliente e do produto no momento da criação do pedido/item para integridade histórica.
* **Autenticação:** Proteção dos endpoints via chave de API (Header `X-API-KEY`).
* **Documentação:** Interface Swagger UI disponível para visualização e teste dos endpoints.
* **Banco de Dados:** Persistência em MySQL 8, gerenciado com SQLAlchemy e Flask-Migrate.
* **CORS:** Configurado para permitir requisições de origens externas (configurável).

## Pré-requisitos

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/) (geralmente incluído na instalação do Docker Desktop)

## Configuração

1.  **Clone o Repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd 2025_api_arq
    ```

2.  **Crie o Arquivo de Ambiente (`.env`):**
    Copie o arquivo `.env.example` (se existir) ou crie um novo arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo, ajustando as senhas:

    ```dotenv
    # ./ .env
    # Configurações do Banco de Dados MySQL
    DB_HOST=db
    DB_PORT=3306
    DB_DATABASE=api_arq_db
    DB_USER=api_arq_user
    DB_PASSWORD=123456
    DB_ROOT_PASSWORD=123456
    
    # Chave de API Simples (para autenticação básica)
    # Gere uma chave aleatória segura para produção
    API_KEY=minha-chave-secreta-123
    ```
    **Importante:** Adicione o arquivo `.env` ao seu `.gitignore` para não versionar informações sensíveis.

## Executando em Desenvolvimento

Este modo utiliza o `docker-compose.override.yml` para habilitar o modo debug do Flask, o log de queries SQL (SQLALCHEMY_ECHO) e geralmente monta volumes para live-reloading do código.

1.  **Construa e Inicie os Containers:**
    Na raiz do projeto, execute:
    ```bash
    docker-compose up --build -d
    ```
    * `--build`: Reconstrói a imagem da API se houver alterações no `Dockerfile` ou `requirements.txt`.
    * `-d`: Executa os containers em segundo plano (detached mode).

2.  **Acesse os Serviços:**
    * **API:** `http://localhost:5000`
    * **Swagger UI:** `http://localhost:5000/apidocs/`
    * **PhpMyAdmin:** `http://localhost:8080` (Use `root` / senha do `DB_ROOT_PASSWORD` ou `api_user` / senha do `DB_PASSWORD` para logar no host `db`).

3.  **Aplicar Migrações (se necessário):**
    Se for a primeira vez ou se houver novas migrações, aplique-as (veja a seção "Gerenciando Migrações").

## Executando em Produção

Este modo utiliza apenas o `docker-compose.yml` base, que deve conter configurações otimizadas para produção (ex: `FLASK_ENV=production`, `FLASK_DEBUG=0`).

1.  **Construa e Inicie os Containers (Especificando o Arquivo Base):**
    Na raiz do projeto, execute:
    ```bash
    docker-compose -f docker-compose.yml up --build -d
    ```
    * `-f docker-compose.yml`: Garante que apenas o arquivo base seja usado, ignorando o `docker-compose.override.yml`.

2.  **Considerações Adicionais para Produção:**
    * **Segurança:** Use senhas fortes e considere mecanismos de gerenciamento de segredos (como Docker Secrets ou variáveis de ambiente injetadas pelo sistema de orquestração). Gere uma `API_KEY` segura.
    * **HTTPS:** Configure um proxy reverso (como Nginx ou Traefik) na frente da API para lidar com HTTPS/TLS.
    * **Origens CORS:** No `app/__init__.py`, substitua `{"origins": "*"}` pela lista explícita de domínios dos seus parceiros permitidos.
    * **WSGI Server:** Para produção, considere usar um servidor WSGI mais robusto como Gunicorn ou uWSGI em vez do servidor de desenvolvimento do Flask. Isso exigiria ajustar o `CMD` no `Dockerfile` e adicionar o servidor ao `requirements.txt`. Exemplo com Gunicorn:
        ```dockerfile
        # Dockerfile (exemplo CMD para produção)
        # Instale gunicorn via requirements.txt
        CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
        ```

## Gerenciando Migrações do Banco de Dados (Flask-Migrate/Alembic)

As migrações permitem evoluir o esquema do banco de dados de forma controlada à medida que os modelos SQLAlchemy são alterados. Os comandos devem ser executados *dentro* do container da API.

1.  **Acessar o Container da API:**
    ```bash
    docker-compose exec api bash
    ```

2.  **Inicializar (Apenas uma vez por projeto):**
    Se a pasta `migrations` ainda não existe.
    ```bash
    flask db init
    ```

3.  **Gerar uma Nova Migração:**
    Após modificar um modelo em `app/models/`.
    ```bash
    flask db migrate -m "Mensagem descritiva da mudança"
    # Ex: flask db migrate -m "Adiciona coluna status a pedido"
    ```
    * Isso cria um novo script na pasta `migrations/versions/`. Revise o script gerado.

4.  **Aplicar Migrações Pendentes ao Banco:**
    ```bash
    flask db upgrade
    ```
    * Executa os scripts de migração que ainda não foram aplicados.

5.  **Reverter a Última Migração (se necessário):**
    ```bash
    flask db downgrade
    ```

6.  **Verificar Status:**
    * `flask db current`: Mostra a revisão atual do banco.
    * `flask db history`: Mostra o histórico de migrações.

## Acessando a API

* **Swagger UI:** `http://localhost:5000/apidocs/` - Interface interativa para explorar e testar os endpoints.
* **Autenticação:** Todas as rotas sob `/api/*` requerem um cabeçalho `X-API-KEY` com o valor definido na variável de ambiente `API_KEY` (no arquivo `.env`).

## Acessando o Banco de Dados

* **PhpMyAdmin:** `http://localhost:8080`
* **Host:** `db` (nome do serviço no Docker Compose)
* **Usuários/Senhas:** Definidos no arquivo `.env` (`DB_USER`, `DB_PASSWORD`, `DB_ROOT_PASSWORD`).

https://gemini.google.com/app/754849c04970fe53

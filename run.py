# ./run.py
# Ponto de entrada principal para iniciar a aplicação Flask.

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Isso garante que as configurações (DB, API_KEY) estejam disponíveis
load_dotenv()

# Importa a função create_app de dentro do pacote 'app'
# A importação é feita DEPOIS de carregar o .env
from app import create_app

# Cria a instância da aplicação Flask chamando a fábrica
app = create_app()

if __name__ == '__main__':
    # Obtém a porta da variável de ambiente ou usa 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    # Executa a aplicação
    # host='0.0.0.0' torna a API acessível externamente (necessário para Docker)
    # debug=True é útil para desenvolvimento, mas deve ser False em produção
    # O modo debug é geralmente controlado pela variável FLASK_ENV no .env/docker-compose
    app.run(host='0.0.0.0', port=port, debug=(os.environ.get('FLASK_ENV') == 'development'))

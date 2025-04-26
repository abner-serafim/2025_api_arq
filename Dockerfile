# Dockerfile
# Define como construir a imagem Docker para a API Flask

# Usa a imagem oficial do Python 3.13 como base
FROM python:3.13-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o diretório de trabalho
COPY requirements.txt .

# Instala as dependências listadas no requirements.txt
# --no-cache-dir: Não armazena o cache do pip, reduzindo o tamanho da imagem
# --upgrade pip: Garante que o pip está atualizado
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
# Assumindo que seu código estará em uma pasta 'app' e um arquivo 'run.py' na raiz
COPY ./app /app/app
COPY ./migrations /app/migrations
COPY ./run.py /app/run.py
# Se tiver outros arquivos/pastas na raiz, copie-os também

# Expõe a porta que a aplicação Flask usará dentro do container
EXPOSE 5000

# Comando padrão para executar a aplicação quando o container iniciar
# Usa 'flask run' que é recomendado para desenvolvimento e alguns cenários de produção simples
# host=0.0.0.0 torna a aplicação acessível externamente ao container
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

FROM python:3.11.8-slim

WORKDIR /app

# Instalar dependências do sistema para o psycopg2
RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiar o arquivo de dependências
COPY requirements.txt /app/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o restante da aplicação para dentro do contêiner
COPY . /app/

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar o app Streamlit
CMD ["streamlit", "run", "Teste.py", "--server.address=0.0.0.0"]

FROM python:3.11.8-slim

WORKDIR /app

# Instalar dependências do sistema para psycopg2 (gcc e libpq-dev)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt /app/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o restante do código
COPY . /app/

# Expor porta padrão do Streamlit
EXPOSE 8501

# Rodar app Streamlit com endereço 0.0.0.0 e modo headless na porta 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

FROM python:3.10-slim

WORKDIR /app

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do container
COPY . .

# Porta padrão (será sobrescrita pelo docker-compose)
EXPOSE 8000
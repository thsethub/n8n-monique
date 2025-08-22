# Etapa 1: Use uma imagem base oficial do Python
FROM python:3.11-slim

# Etapa 2: Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Etapa 3: Copie o arquivo de dependências e instale-as
# Fazemos isso separadamente para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 4: Copie o código da sua aplicação para o contêiner
COPY . .

# Etapa 5: Comando para executar a API quando o contêiner iniciar
# Uvicorn precisa rodar em 0.0.0.0 para ser acessível de fora do contêiner
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8181"]
# Usa uma imagem leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências primeiro para instalar os pacotes antes do código
COPY requirements.txt /app/requirements.txt

# Instala as dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Agora copia o código do Django para o contêiner
COPY ./myproject /app

# Expõe a porta que o Django usará
EXPOSE 8000

# Comando para iniciar o Gunicorn apontando para o WSGI correto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]

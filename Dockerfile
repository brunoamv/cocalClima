# Usa uma imagem leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Instala FFmpeg e dependências necessárias
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências primeiro para instalar os pacotes antes do código
COPY requirements.txt /app/requirements.txt

COPY nginx/static/robots.txt /etc/nginx/static/robots.txt
COPY nginx/static/sitemap.xml /etc/nginx/static/sitemap.xml

# Instala as dependências Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Agora copia o código do Django para o contêiner
COPY ./myproject /app

# Expõe a porta que o Django usará
EXPOSE 8000

# Comando para iniciar o Gunicorn apontando para o WSGI correto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]

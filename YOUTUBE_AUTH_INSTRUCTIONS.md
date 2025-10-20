# 🔐 YouTube Authentication - Instruções Completas

## ⚠️ Problema Identificado
O script `generate_youtube_token.py` falha porque faltam dependências Python no sistema local.

## ✅ Soluções Disponíveis

### 🎯 Solução 1: OAuth Playground (RECOMENDADA)
**Mais fácil e funciona sempre:**

1. **Abra o OAuth Playground:**
   - Vá para: https://developers.google.com/oauthplayground

2. **Configure o Playground:**
   - No lado direito, clique em ⚙️ **OAuth 2.0 configuration**
   - Marque ☑️ **Use your own OAuth credentials**
   - Cole seu **Client ID** e **Client secret** do arquivo `client_secret.json`

3. **Autorize a API:**
   - No lado esquerdo, em **Select & authorize APIs**
   - Digite: `https://www.googleapis.com/auth/youtube`
   - Clique **Authorize APIs**
   - Faça login na conta Google associada ao YouTube

4. **Gere o Token:**
   - Clique **Exchange authorization code for tokens**
   - Copie o **Refresh token** gerado

5. **Crie o arquivo token.json:**
```json
{
  "token": "ACCESS_TOKEN_AQUI",

  
  "refresh_token": "REFRESH_TOKEN_AQUI",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "SEU_CLIENT_ID",
  "client_secret": "SEU_CLIENT_SECRET",
  "scopes": ["https://www.googleapis.com/auth/youtube"]
}
```

6. **Salve o arquivo:**
   - Salve como `youtube/credentials/token.json`
   - Reinicie: `docker-compose restart youtube-automation`

### 🐳 Solução 2: Via Container (Avançada)
```bash
# Execute o script helper que criei:
./auth_youtube_container.sh
```

### 💻 Solução 3: Instalar Dependências Localmente
```bash
# Instalar python3-venv primeiro:
sudo apt install python3.11-venv

# Criar ambiente virtual:
python3 -m venv youtube_auth_env
source youtube_auth_env/bin/activate

# Instalar dependências:
pip install google-auth-oauthlib google-api-python-client

# Executar script:
python3 generate_youtube_token.py

# Limpar ambiente:
deactivate
rm -rf youtube_auth_env
```

## 🔍 Verificação Final

Após gerar o token:

```bash
# Verificar se token existe:
ls -la youtube/credentials/token.json

# Reiniciar container:
docker-compose restart youtube-automation

# Verificar logs:
docker-compose logs -f youtube-automation
```

## 📊 Status dos Containers Atual

| Container | Status | Porta | Detalhes |
|-----------|--------|-------|----------|
| **climacocal_app** | ✅ Running | 8000 | Django seguro |
| **climacocal_db** | ✅ Running | 5432 | PostgreSQL OK |
| **camera_streamer** | ✅ Running | 8001 | Dashboard ativo |
| **youtube_automation** | 🔄 Building | - | Aguarda token |

## 🎉 Sistema Está Funcionando!

**Segurança corrigida ✅:**
- DEBUG=False em produção
- ALLOWED_HOSTS restrito
- Credenciais em variáveis de ambiente

**Só falta:** Token de autenticação YouTube para automação completa.

**Recomendação:** Use a **Solução 1 (OAuth Playground)** - é a mais simples e confiável!
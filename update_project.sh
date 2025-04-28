#!/bin/bash

# Arquivos e Configurações
PROJECT_DIR="/home/bruno/cocalClima"
LOG_FILE="$PROJECT_DIR/update_project.log"
GIT_BIN="/usr/bin/git"
DOCKER_COMPOSE_BIN="/usr/bin/docker-compose"
DOCKER_BIN="/usr/bin/docker"

# Configurações de E-mail
EMAIL_TO="bruno.amv@gmail.com"
MAIL_BIN="/usr/bin/mail"  # comando 'mail' instalado via 'mailutils'
SUBJECT_SUCCESS="✅ Update Automático Concluído com Sucesso"
SUBJECT_ERROR="❌ Erro no Update Automático do Servidor"

# Função para logar mensagens
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para enviar e-mail
send_email() {
    local subject="$1"
    if [ -x "$MAIL_BIN" ]; then
        tail -n 50 "$LOG_FILE" | $MAIL_BIN -s "$subject" "$EMAIL_TO"
        log "E-mail enviado: $subject"
    else
        log "ERRO: Comando 'mail' não encontrado. Não foi possível enviar o e-mail."
    fi
}

# =========== SCRIPT COMEÇA AQUI ===========

log "==== Iniciando update automático ===="

cd "$PROJECT_DIR" || { log "ERRO: Falha ao entrar no diretório $PROJECT_DIR"; send_email "$SUBJECT_ERROR"; exit 1; }

# Atualizar repositório
log "Executando git fetch..."
if ! $GIT_BIN fetch origin; then
    log "ERRO: git fetch falhou."
    send_email "$SUBJECT_ERROR"
    exit 1
fi

# Verificar se há atualizações
LOCAL_HASH=$($GIT_BIN rev-parse HEAD)
REMOTE_HASH=$($GIT_BIN rev-parse origin/main)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    log "Atualizações encontradas. Executando git pull..."
    if $GIT_BIN pull; then
        log "git pull concluído com sucesso."

        # Derrubar containers
        log "Derrubando containers atuais..."
        if ! $DOCKER_COMPOSE_BIN down; then
            log "ERRO: docker-compose down falhou."
            send_email "$SUBJECT_ERROR"
            exit 1
        fi

        # Subir containers atualizados
        log "Subindo containers atualizados..."
        if ! $DOCKER_COMPOSE_BIN up -d --build; then
            log "ERRO: docker-compose up --build falhou."
            send_email "$SUBJECT_ERROR"
            exit 1
        fi

        log "Servidor atualizado e containers reiniciados com sucesso."
        send_email "$SUBJECT_SUCCESS"
    else
        log "ERRO: git pull falhou."
        send_email "$SUBJECT_ERROR"
        exit 1
    fi
else
    log "Nenhuma atualização encontrada. Nenhuma ação necessária."
    send_email "$SUBJECT_SUCCESS"
fi





log "==== Fim do update automático ===="
exit 0
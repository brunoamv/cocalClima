#!/bin/bash

# Caminhos e configurações
PROJECT_DIR="/home/bruno/cocalClima"
LOG_DIR="$PROJECT_DIR/scripts/logs"
LOG_FILE="$LOG_DIR/update_project_$(date '+%Y-%m-%d_%H-%M-%S').log"
GIT_BIN="/usr/bin/git"
DOCKER_COMPOSE_BIN="/usr/bin/docker-compose"
DOCKER_BIN="/usr/bin/docker"
MSMTP_BIN="/usr/bin/msmtp"

# E-mail via msmtp
EMAIL_TO="bruno.amv@gmail.com"
EMAIL_ACCOUNT="brevo"  # nome da conta no ~/.msmtprc

# Cria diretório de logs se não existir
mkdir -p "$LOG_DIR"

# Função para logar
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Envia e-mail como texto puro (evita html e = quebras)
send_email() {
    local subject="$1"
    {
        echo "Subject: $subject"
        echo "To: $EMAIL_TO"
        echo "Content-Type: text/plain; charset=UTF-8"
        echo
        tail -n 50 "$LOG_FILE"
    } | $MSMTP_BIN -a "$EMAIL_ACCOUNT" "$EMAIL_TO"
    log "E-mail enviado com assunto: $subject"
}

# Início do processo
log "==== Iniciando update Automático ===="

cd "$PROJECT_DIR" || {
    log "ERRO: Falha ao entrar no diretório $PROJECT_DIR"
    send_email "❌ Erro no Update Automático"
    exit 1
}

log "Executando git fetch..."
if ! $GIT_BIN fetch origin; then
    log "ERRO: git fetch falhou."
    send_email "❌ Erro no Update Automático"
    exit 1
fi

LOCAL_HASH=$($GIT_BIN rev-parse HEAD)
REMOTE_HASH=$($GIT_BIN rev-parse origin/main)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    log "Atualizações encontradas. Executando git pull..."
    if $GIT_BIN pull; then
        log "git pull concluído com sucesso."

        log "Derrubando containers atuais..."
        if ! $DOCKER_COMPOSE_BIN down; then
            log "ERRO: docker-compose down falhou."
            send_email "❌ Erro no Update Automático"
            exit 1
        fi

        log "Subindo containers atualizados..."
        if ! $DOCKER_COMPOSE_BIN up -d --build; then
            log "ERRO: docker-compose up --build falhou."
            send_email "❌ Erro no Update Automático"
            exit 1
        fi

        log "Servidor atualizado e containers reiniciados com sucesso."
        log "==== Fim do update Automático ===="
        send_email "✅ Update Automático Concluído com Sucesso"
    else
        log "ERRO: git pull falhou."
        log "==== Fim do update Automático ===="
        send_email "❌ Erro no Update Automático"
        exit 1
    fi
else
    log "Nenhuma atualização encontrada. Nenhuma ação necessária."
    log "==== Fim do update Automático ===="
    send_email "❌ Update Automático SEM ALTERAÇÃO"
fi

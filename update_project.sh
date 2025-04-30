#!/bin/bash

# Caminhos e configurações
PROJECT_DIR="/home/bruno/cocalClima"
LOG_FILE="$PROJECT_DIR/update_project.log"
GIT_BIN="/usr/bin/git"
DOCKER_COMPOSE_BIN="/usr/bin/docker-compose"
DOCKER_BIN="/usr/bin/docker"
MSMTP_BIN="/usr/bin/msmtp"

# E-mail via msmtp
EMAIL_TO="bruno.amv@gmail.com"
EMAIL_ACCOUNT="brevo"  # nome da conta no ~/.msmtprc

# Funcao para logar
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

# Inicio do processo
log "==== Iniciando update Automatico ===="

cd "$PROJECT_DIR" || {
    log "ERRO: Falha ao entrar no diretório $PROJECT_DIR"
    send_email "❌ Erro no Update Automatico"
    exit 1
}

log "Executando git fetch..."
if ! $GIT_BIN fetch origin; then
    log "ERRO: git fetch falhou."
    send_email "❌ Erro no Update Automatico"
    exit 1
fi

LOCAL_HASH=$($GIT_BIN rev-parse HEAD)
REMOTE_HASH=$($GIT_BIN rev-parse origin/main)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    log "Atualizações encontradas. Executando git pull..."
    if $GIT_BIN pull; then
        log "git pull concluido com sucesso."

        log "Derrubando containers atuais..."
        if ! $DOCKER_COMPOSE_BIN down; then
            log "ERRO: docker-compose down falhou."
            send_email "❌ Erro no Update Automatico"
            exit 1
        fi

        log "Subindo containers atualizados..."
        if ! $DOCKER_COMPOSE_BIN up -d --build; then
            log "ERRO: docker-compose up --build falhou."
            send_email "❌ Erro no Update Automatico"
            exit 1
        fi

        log "Servidor atualizado e containers reiniciados com sucesso."
        log "==== Fim do update Automatico ===="
        send_email "✅ Update Automatico Concluido com Sucesso"
    else
        log "ERRO: git pull falhou."
        log "==== Fim do update Automatico ===="
        send_email "❌ Erro no Update Automatico"
        exit 1
    fi
else
    log "Nenhuma atualizacao encontrada. Nenhuma acao necessaria."
    log "==== Fim do update Automatico ===="
    send_email "❌ Update Automatico SEM ALTERACAO"
fi



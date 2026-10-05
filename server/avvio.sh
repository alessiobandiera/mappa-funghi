#!/bin/sh
# Prepara la copia del repository nel volume /repo al primo avvio, poi lancia il comando (di norma supercronic).
set -eu

: "${REPO_URL:=git@github.com:alessiobandiera/mappa-funghi.git}"
: "${GIT_NOME:=mappa-funghi server}"
: "${GIT_EMAIL:=mappa-funghi-server@users.noreply.github.com}"

if [ -f /run/secrets/deploy_key ]; then
    mkdir -p /root/.ssh
    cp /run/secrets/deploy_key /root/.ssh/id_deploy
    chmod 600 /root/.ssh/id_deploy
    export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_deploy -o StrictHostKeyChecking=accept-new"
fi

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Primo avvio: clono $REPO_URL in $REPO_DIR"
    git clone -q "$REPO_URL" "$REPO_DIR"
fi
git -C "$REPO_DIR" config user.name "$GIT_NOME"
git -C "$REPO_DIR" config user.email "$GIT_EMAIL"
git config --global --add safe.directory "$REPO_DIR"

mkdir -p "$DATI_DIR"
# così anche i giri lanciati da supercronic vedono la chiave
[ -n "${GIT_SSH_COMMAND:-}" ] && echo "export GIT_SSH_COMMAND=\"$GIT_SSH_COMMAND\"" > /app/.ambiente || : > /app/.ambiente

exec "$@"

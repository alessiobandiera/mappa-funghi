#!/bin/sh
# Un giro di aggiornamento: completo | leggero | archivio
#   PUBBLICA=1  committa e fa push su main (GitHub Actions pubblica poi su Pages)
#   PUBBLICA=0  prova: nessun push, l'uscita viene copiata in /dati/prova per confrontarla con quella delle Actions
set -eu
MODO="${1:?uso: giro.sh completo|leggero|archivio}"
[ -f /app/.ambiente ] && . /app/.ambiente
: "${PUBBLICA:=0}"
: "${BUDGET_ARCHIVIO_S:=2400}"
export BUDGET_ARCHIVIO_S

# un giro alla volta: se il precedente non ha finito, questo si salta
exec 9>/tmp/giro.lock
if ! flock -n 9; then echo "$(date '+%F %T') giro $MODO saltato: un altro è ancora in corso"; exit 0; fi

cd "$REPO_DIR"
echo "$(date '+%F %T') inizio giro $MODO (PUBBLICA=$PUBBLICA)"

if [ "$PUBBLICA" = "1" ]; then
    git pull -q --rebase origin main
else
    # in prova si riparte sempre dallo stato di GitHub, senza toccarlo
    git fetch -q origin main && git reset -q --hard origin/main
fi

case "$MODO" in
    completo|leggero)
        python script/aggiorna.py "--$MODO" ;;
    archivio)
        python - <<'PY'
import os, sys
sys.path.insert(0, "script")
import aggiorna as a
from datetime import datetime
a.log("Archivio stazioni:", a.archivia_db(datetime.now(a.ROMA).date(),
                                          budget_s=float(os.environ["BUDGET_ARCHIVIO_S"])))
PY
        ;;
    *) echo "modo sconosciuto: $MODO"; exit 2 ;;
esac

python /app/db.py || echo "Database non aggiornato (il giro prosegue)"

if [ "$PUBBLICA" = "1" ]; then
    git add docs/dati data
    if git diff --cached --quiet; then
        echo "Nessuna novità da pubblicare"
    else
        git commit -q -m "Dati del $(date '+%Y-%m-%d %H:%M') ($MODO, server)"
        git pull -q --rebase origin main
        git push -q origin HEAD:main
        echo "Pubblicato"
    fi
else
    mkdir -p "$DATI_DIR/prova"
    cp -r docs/dati data/db/ultimo_giro.json "$DATI_DIR/prova/" 2>/dev/null || true
    echo "Prova: uscita copiata in $DATI_DIR/prova"
fi
echo "$(date '+%F %T') fine giro $MODO"

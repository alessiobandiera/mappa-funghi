# App «Raccolte» per iPhone

Le stesse pagine del sito (`docs/raccolte.html`, `index.html`, `bosco.html`) dentro un'app Capacitor, per un solo motivo:
registrare il percorso del giro **anche a schermo spento** (plugin `@capacitor-community/background-geolocation`).
Il codice è pubblico; i dati dell'utente restano nell'app e nel suo archivio privato.

- `prepara.mjs` copia le pagine in `www/`, aggiunge `capacitor.js` e `app-nativa.js`, mette Leaflet dentro l'app e cambia i
  collegamenti `./` in `index.html` (nell'app la pagina iniziale è `raccolte.html`, `server.appStartPath`).
- `app-nativa.js` (solo nell'app): dati e tessere dal sito pubblicato con copia per quando manca la rete (IndexedDB
  «app-copie»), sfondo delle mappe già visto, zone a 20 m salvate (`window.AppCopie`).
- Nelle pagine: `window.APP_NATIVA` e `capacitorExports.registerPlugin("BackgroundGeolocation")` in `raccolte.html`.
- Costruzione: workflow `app-ios.yml` (a mano) su un Mac di GitHub, senza firma → release `app-iphone-…` con `Raccolte.ipa`.
- Installazione: AltStore (AltServer su un PC di casa) firma l'app con l'ID Apple gratuito dell'utente: dura 7 giorni e AltServer
  la rinnova da solo quando iPhone e PC sono sulla stessa rete Wi-Fi.

Prova locale delle pagine: `npm ci && node prepara.mjs`, poi servire `www/` (fuori dall'app `app-nativa.js` non fa niente).

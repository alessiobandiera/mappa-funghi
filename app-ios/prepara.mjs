// Prepara app-ios/www dalle pagine del sito (docs/): le stesse pagine, con in più Capacitor e app-nativa.js, Leaflet dentro
// l'app (si apre anche senza rete) e i collegamenti fra le pagine con il nome del file (nell'app la pagina iniziale è raccolte.html).
// Ogni sostituzione deve trovare il suo testo: se una pagina cambia e il testo non c'è più, si ferma con un errore.
// Uso: node prepara.mjs   (da app-ios/, dopo npm ci)
import fs from "node:fs";
import path from "node:path";

const QUI = path.dirname(new URL(import.meta.url).pathname), DOCS = path.join(QUI, "..", "docs"), WWW = path.join(QUI, "www");
fs.rmSync(WWW, { recursive: true, force: true }); fs.mkdirSync(path.join(WWW, "lib", "images"), { recursive: true });

for (const f of ["foglio.js", "porcini.js", "stile.css", "mappa-piena.js", "raccolte-icona-180.png", "raccolte-icona-512.png"])
  fs.copyFileSync(path.join(DOCS, f), path.join(WWW, f));
const nm = p => path.join(QUI, "node_modules", p);
fs.copyFileSync(nm("@capacitor/core/dist/capacitor.js"), path.join(WWW, "capacitor.js"));
fs.copyFileSync(nm("leaflet/dist/leaflet.js"), path.join(WWW, "lib", "leaflet.js"));
fs.copyFileSync(nm("leaflet/dist/leaflet.css"), path.join(WWW, "lib", "leaflet.css"));
for (const f of fs.readdirSync(nm("leaflet/dist/images"))) fs.copyFileSync(path.join(nm("leaflet/dist/images"), f), path.join(WWW, "lib", "images", f));
fs.copyFileSync(path.join(QUI, "app-nativa.js"), path.join(WWW, "app-nativa.js"));

const CDN_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js", CDN_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";
function sostituisci(testo, file, da, a, volte = 1) {
  const n = testo.split(da).length - 1;
  if (n !== volte) throw new Error(`${file}: «${da}» trovato ${n} volte invece di ${volte}`);
  return testo.split(da).join(a);
}
const PAGINE = {
  "raccolte.html": [[CDN_JS, "lib/leaflet.js"], [CDN_CSS, "lib/leaflet.css"], ['href="./" style', 'href="index.html" style'], ['frame.src = "./";', 'frame.src = "index.html";']],
  "index.html": [[CDN_JS, "lib/leaflet.js"], [CDN_CSS, "lib/leaflet.css"]],
  "bosco.html": [[CDN_JS, "lib/leaflet.js"], [CDN_CSS, "lib/leaflet.css"], ['<a class="vai" href="./">', '<a class="vai" href="index.html">'], ["a.href=`./#", "a.href=`index.html#"]],
};
for (const [f, regole] of Object.entries(PAGINE)) {
  let t = fs.readFileSync(path.join(DOCS, f), "utf8");
  for (const [da, a] of regole) t = sostituisci(t, f, da, a);
  // Capacitor e app-nativa.js per primi, prima di ogni altro script della pagina
  t = sostituisci(t, f, '<meta charset="utf-8">', '<meta charset="utf-8">\n<script src="capacitor.js"></script>\n<script src="app-nativa.js"></script>');
  fs.writeFileSync(path.join(WWW, f), t);
}
console.log("www pronta:", fs.readdirSync(WWW).join(", "));

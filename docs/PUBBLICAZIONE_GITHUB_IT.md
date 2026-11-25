# Pubblicare Nuvio Control Center su GitHub (guida completa)

Questa guida riguarda solo il **codice del Control Center**. Nuvio TV ha il proprio repository e la propria licenza (GPL-3.0); questo progetto ne scarica le release ufficiali e non le ridistribuisce.

I comandi sono pensati per il tuo **server Debian** (dove hai già il progetto), ma funzionano uguali su qualsiasi Linux. In fondo c'è la variante Windows.

---

## 0. Controllo di sicurezza prima di caricare

Lavora **sempre sulla cartella estratta dallo ZIP**, mai su `/opt/nuvio-updater` o `/var/lib/nuvio-updater` (lì ci sono password, chiavi e stato reali).

```bash
cd ~/Nuvio-Control-Center
# Nessun file privato deve comparire qui sotto:
find . \( -name 'auth.json' -o -name 'config.json' -o -name 'state.json' -o -name '*_webos' -o -name '*.ipk' -o -name '.ssh' \) -print
# Nessun IP reale di casa tua (gli esempi 192.168.1.50/51 e 192.0.2.x vanno bene):
grep -rnE '192\.168\.[0-9]+\.[0-9]+' . | grep -vE '192\.168\.1\.5[01]'
```

Se i due comandi non stampano nulla, sei a posto. `.gitignore` blocca comunque questi file anche se finissero nella cartella per errore.

## 1. Account e repository

1. Se non lo hai, crea l'account su https://github.com/signup.
2. **Privacy email:** Settings → Emails → spunta **Keep my email addresses private**. Copia l'indirizzo `NUMERO+utente@users.noreply.github.com` che ti mostra: lo userai nei commit, così la tua email personale non diventa pubblica.
3. Crea il repository: https://github.com/new
   - Repository name: `Nuvio-Control-Center`
   - Description: `Self-hosted dashboard to keep Nuvio TV updated on LG webOS (Developer Mode) - Linux, Windows`
   - **Public**
   - **NON** spuntare *Add a README*, *.gitignore* o *license* (li abbiamo già: un repository non vuoto fa fallire il primo push).
   - Create repository.

## 2. Autenticazione di Git verso GitHub (una volta sola)

GitHub non accetta più la password dell'account per `git push`. Scegli **una** delle due strade.

**A. Chiave SSH (consigliata su un server)**

```bash
ssh-keygen -t ed25519 -C "github-nuvio" -f ~/.ssh/id_ed25519_github
cat ~/.ssh/id_ed25519_github.pub
```

Copia la riga stampata in GitHub → Settings → **SSH and GPG keys** → **New SSH key** (Type: Authentication key). Poi:

```bash
cat >> ~/.ssh/config <<'EOF'
Host github.com
  IdentityFile ~/.ssh/id_ed25519_github
  IdentitiesOnly yes
EOF
ssh -T git@github.com     # rispondi "yes"; deve dire "Hi lucairr! You've successfully authenticated"
```

**B. GitHub CLI** (Debian 12+/Ubuntu: `sudo apt install gh`)

```bash
gh auth login    # GitHub.com -> HTTPS -> Login with a web browser, incolla il codice mostrato
```

## 3. Nome utente nei file

I file del progetto usano già l'utente `lucairr` (link nel README/post e `.github/FUNDING.yml`). Se pubblichi da un altro account:

```bash
grep -rl 'lucairr' . --exclude-dir=.git | xargs sed -i 's/lucairr/ALTRO_UTENTE/g'
```

Apri `.github/FUNDING.yml` e **togli il `#` solo dalle piattaforme che hai davvero attivato** (vedi punto 7). Se non ne hai ancora nessuna, lascia il file così: non fa danni.

## 4. Primo commit e push

```bash
cd ~/Nuvio-Control-Center
sudo apt install -y git            # se manca
git config --global user.name  "Luca Sfano"
git config --global user.email "NUMERO+utente@users.noreply.github.com"   # quella del punto 1.2

git init -b main
git add .
git status                          # controlla l'elenco: niente auth.json/config.json/state.json/.ssh
git commit -m "Nuvio Control Center 1.2.0-beta - first public release"

# SSH (strada A):
git remote add origin git@github.com:lucairr/Nuvio-Control-Center.git
# oppure HTTPS con gh (strada B):
# git remote add origin https://github.com/lucairr/Nuvio-Control-Center.git

git push -u origin main
```

Ricarica la pagina del repository: devi vedere il README con le istruzioni.

## 5. Impostazioni del repository (5 minuti)

- **About** (ingranaggio a destra della pagina principale): Topics `lg-webos`, `webos`, `nuvio`, `smart-tv`, `self-hosted`, `homelab`, `updater`.
- **Settings → General → Features:** lascia *Issues* attivo; puoi disattivare *Wiki* e *Projects*.
- **Settings → Code security → Private vulnerability reporting → Enable** (SECURITY.md rimanda lì).
- **Settings → Actions → General:** *Allow all actions*. Il workflow di release chiede da solo il permesso `contents: write`.

## 6. Controlla GitHub Actions

Scheda **Actions** → workflow **Tests**. Deve diventare verde:

- unit test su Ubuntu (Python 3.13 e 3.9) e Windows (Python 3.9 e 3.13);
- sintassi degli script shell;
- **parse degli script PowerShell con Windows PowerShell 5.1 e PowerShell 7** e controllo caratteri ASCII;
- smoke test delle funzioni Windows (ricerca di Python/pythonw e npm).

Se qualcosa è rosso, apri il job, copia l'errore e sistemalo prima di pubblicare la release. **CI verde non significa che l'aggiornamento reale su una TV sia validato**: per Windows serve almeno un test vero (installazione, associazione TV, Verifica aggiornamenti).

## 7. Donazioni volontarie

Il pulsante **Sponsor** compare quando `.github/FUNDING.yml` contiene almeno una piattaforma attiva.

| Piattaforma | Commissione sulle donazioni | Note |
| --- | --- | --- |
| **Ko-fi** (`ko_fi:`) | 0% (restano le fee PayPal/Stripe) | Si attiva in 10 minuti, ideale per partire |
| **GitHub Sponsors** (`github:`) | 0% per account personali | Richiede profilo Stripe e approvazione, può richiedere qualche giorno |
| Buy Me a Coffee (`buy_me_a_coffee:`) | 5% | Molto noto |
| PayPal.me (`custom:`) | fee PayPal | Semplice, ma espone il nome del conto |

Esempio dopo aver creato Ko-fi:

```yaml
ko_fi: lucairr
```

Poi `git add .github/FUNDING.yml && git commit -m "Enable sponsor button" && git push`. Le donazioni non devono sbloccare funzioni: il progetto resta gratuito (così anche nel README). Se gli importi diventano regolari, chiedi al tuo commercialista come dichiararli.

## 8. Pubblica la prima release (beta)

Quando la CI è verde e hai fatto almeno il test Windows reale:

```bash
git tag -a v1.2.0-beta -m "Nuvio Control Center 1.2.0-beta"
git push origin v1.2.0-beta
```

Il workflow **Release archives**:

1. verifica che il tag corrisponda a `VERSION` in `nuvio/core.py` e che `CHANGELOG.md` abbia la sezione `## 1.2.0-beta`;
2. riesegue i test;
3. crea la Release **marcata come pre-release** (il tag contiene `-beta`) con ZIP, TAR.GZ e `SHA256SUMS.txt`. Nello ZIP gli script Windows hanno già i fine riga CRLF.

Il link da dare agli utenti diventa `https://github.com/lucairr/Nuvio-Control-Center/releases/latest`.

## 9. Versioni successive

1. Modifica il codice, aggiorna `VERSION` in `nuvio/core.py` (es. `1.3.0-beta`) e aggiungi `## 1.3.0-beta — data` in `CHANGELOG.md`.
2. `python3 -m unittest discover -s tests -v`
3. `git commit -am "..." && git push`
4. `git tag -a v1.3.0-beta -m "..." && git push origin v1.3.0-beta`

Se il tag non corrisponde a `VERSION`, il workflow si ferma prima di pubblicare: è voluto.

---

## Variante: pubblicare da Windows

1. Installa **Git for Windows** (https://git-scm.com/download/win, opzioni predefinite: include *Git Credential Manager*, che apre il browser per il login a GitHub al primo push).
2. Apri **Git Bash** nella cartella estratta e usa gli stessi comandi del punto 4 con il remote HTTPS.

**Non usare** il caricamento drag-and-drop dal sito: i browser saltano spesso i file e le cartelle che iniziano con il punto (`.github`, `.gitignore`, `.gitattributes`) e la CI/release non funzionerebbero.

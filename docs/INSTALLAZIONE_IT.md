# Guida italiana — Nuvio Control Center

Nuvio Control Center è un pannello web **indipendente e non ufficiale** per controllare e aggiornare **Nuvio TV su LG webOS**, usando l'app Developer Mode. È pensato per chi ha **già installato Nuvio**. Per la prima installazione utilizza l'[installer ufficiale](https://github.com/NuvioMedia/NuvioTVSmart-Installer).

## Cosa include

- **Verifica aggiornamenti**: confronta Nuvio sulla TV con l'ultima release pubblicata da NuvioMedia, senza installare nulla.
- **Installa aggiornamento**: installa un IPK nuovo dopo aver verificato ID app e versione.
- **Forza installazione**: reinstallazione manuale dell'ultima release con conferma.
- **Versioni precedenti / Downgrade**: elenco delle release ufficiali con IPK, scelta manuale di una versione più vecchia e conferma obbligatoria. L'auto-update viene disattivato quando avvii il downgrade.
- **Automatico opzionale**: controllo tutti i giorni alle 19:30, installazione solo se la versione TV è nota e c'è un aggiornamento.
- **Dashboard** con login, stato TV, note delle release, storico e log.

## Requisiti

Python 3.9+, Node.js 20+ (consigliato Node 22), `npm`, rete verso la TV e Internet per GitHub. Sul televisore: **Developer Mode ON** e **Key Server ON**. Nuvio deve già essere presente (`space.nuvio.webos`).

## Installazione Linux (Debian / Ubuntu)

Dopo aver scaricato e scompattato lo ZIP di GitHub nella macchina Linux:

```bash
node -v
sudo TV_IP=192.168.1.50 bash install.sh
sudo bash scripts/connect-tv-linux.sh 192.168.1.50
```

Sostituisci l'IP di esempio con quello **mostrato dall'app Developer Mode sulla LG**. Durante il comando `--getkey`, quando compare `input passphrase:`, digita **solo il codice visualizzato sulla TV** e premi Invio. Non incollare comandi nel prompt della passphrase.

Apri `http://IP_DEL_SERVER:8765`. La password è quella scelta nell'installazione.

Se sulla tua Debian hai ancora **Node 12**, installa Node.js 22 usando le istruzioni NodeSource prima di eseguire `install.sh`: [guida dettagliata Linux](INSTALL_LINUX.md).

## Installazione PC Windows 10/11

1. Installa **Python 3.9+** da [python.org](https://www.python.org/downloads/windows/) spuntando **"Add python.exe to PATH"** e **Node.js LTS** da [nodejs.org](https://nodejs.org/). Poi chiudi e riapri le finestre aperte.
2. Scarica lo ZIP del repository (Code → Download ZIP oppure da **Releases**) ed **estrailo** (tasto destro → *Estrai tutto*).
3. Nella cartella estratta fai **doppio clic su `install-windows.cmd`**. Ti chiederà l'**IP della TV**, la **password della dashboard** (min. 12 caratteri) e se vuoi **associare subito la TV**: rispondi Invio e digita la **passphrase mostrata dalla TV**.

Da PowerShell, in alternativa:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install-windows.ps1 -TvIp 192.168.1.50 -Pair
```

Non servono privilegi di amministratore: il CLI LG viene installato in automatico per il tuo utente. Vengono create due attività pianificate (dashboard all'accesso e controllo alle 19:30, anche a batteria) e il collegamento **Nuvio Control Center** sul Desktop (`http://localhost:8765`). Il PC deve essere acceso con l'utente connesso; i controlli saltati partono al successivo accesso.

- **Riassociare la TV** (cambio IP, nuova chiave): `connect-tv-windows.ps1` in `%LOCALAPPDATA%\NuvioControlCenter` aggiorna sia il profilo LG sia `config.json`.
- **Diagnostica**: `doctor.ps1` nella stessa cartella (non modifica nulla sulla TV).
- **Accesso da telefono/altri PC**: aggiungi `-AllowLan`; ti verrà proposta una regola firewall limitata alle reti *Private* e alla sottorete locale.

[Guida Windows completa](INSTALL_WINDOWS.md).

## Altri dispositivi e sistemi

- **Raspberry Pi 4/5 (solo 64-bit)**: installazione Debian/systemd o Docker; **compatibilità della CLI LG su ARM64 non ancora verificata**.
- **NAS Synology, QNAP e Linux Docker**: procedura sperimentale in [guida Docker](INSTALL_DOCKER.md), con dati e chiavi SSH in un volume persistente.
- **macOS Intel / Apple Silicon**: installer `macos/install-macos.sh`, `launchd`, istruzioni in [guida macOS](INSTALL_MACOS.md), non ancora verificato su hardware reale.
- **Mini PC / NUC / Proxmox**: usa la guida Debian/Ubuntu per una VM Linux standard; anche Docker è opzionale.

[Compatibilità hardware e stato test](HARDWARE_COMPATIBILITY.md).

## Versioni precedenti (downgrade manuale)

Prima esegui **Verifica aggiornamenti**. Se viene letta la versione installata, apri **Versioni precedenti → Carica release**; scegli un IPK di una release ufficiale con numero strettamente inferiore, leggi l'avviso e conferma l'installazione. **Il downgrade è manuale**, non disinstalla Nuvio e non agisce sul firmware LG. Si interrompe se webOS rifiuta la versione vecchia. Possibili incompatibilità delle impostazioni: effettua un backup quando disponibile. Dopo l'avvio del downgrade gli aggiornamenti automatici vengono disabilitati, così non tornerai immediatamente all'ultima release.

## Prima verifica e automazione

Apri la dashboard e premi **Verifica aggiornamenti**. Verifica che sia visibile la versione già installata e che la TV risulti collegata. Soltanto dopo attiva lo switch **Installazione automatica**. Se la versione è ignota o la TV è offline, l'auto-update non installa nulla. **Forza installazione** è invece un'azione manuale da usare dopo la verifica.

## Se cambia l'IP del televisore

L'IP va modificato **sia nella configurazione della CLI LG** (`ares-setup-device --modify nuvio-lg --info host=NUOVO_IP`) **sia nel file `config.json` del Control Center**. Linux: `/var/lib/nuvio-updater/config.json`; Windows: `%USERPROFILE%\.nuvio-control-center\config.json` (su Windows `connect-tv-windows.ps1` aggiorna entrambi in automatico). Consigliata una prenotazione DHCP sul router.

## Problemi comuni

- **No matched device nuvio-lg**: hai eseguito il comando con un utente diverso da quello con cui hai associato la TV. Su Debian usa `sudo runuser -u nuvio-updater -- env HOME=/var/lib/nuvio-updater ...`.
- **Failed to get ssh private key**: controlla IP effettivo su Developer Mode, Key Server attivo e porta 9991 raggiungibile; poi ripeti `--getkey`.
- **TV raggiungibile ma versione sconosciuta**: l'updater non procede automaticamente; verifica `ares-install --listfull` e i log della dashboard.
- **Dev Mode scaduto**: riattivalo dalla TV. Il progetto non aggira la scadenza dell'app LG.

[Altri dettagli tecnici](TROUBLESHOOTING.md).

## Sicurezza e limiti

Non aprire la porta **8765** su Internet: si tratta di HTTP senza cifratura nativa, destinato a localhost o LAN fidate. Per accesso remoto usa VPN o HTTPS reverse proxy. Password e chiavi sono salvate **localmente**, non in GitHub. Non pubblicare `config.json`, `auth.json` o i file `.ssh` nei report di errore. Questo pacchetto è in **beta** e non è stato ancora validato con un ciclo reale completo su tutte le versioni di LG webOS.

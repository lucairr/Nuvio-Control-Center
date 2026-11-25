# Piano di test prima del rilascio pubblico

**Non serve testare subito ogni piattaforma.** Il primo obiettivo è conservare il funzionamento sulla VM Debian già nota; le altre piattaforme vanno dichiarate sperimentali finché non vengono effettivamente provate.

## Ordine consigliato

| Test | Operazione | Esito da annotare |
|---|---|---|
| 1. Installazione/upgrade host | Installa il pacchetto su host di prova, senza perdere configurazione preesistente | OK / errore / backup |
| 2. Accesso dashboard | Login, logout, login errato, nuova sessione dopo restart | Nessun accesso non autorizzato |
| 3. CLI LG | Associa TV nella **stessa utenza** in cui gira il servizio | `ares-install --listfull` legge Nuvio |
| 4. Verifica | Premi **Verifica aggiornamenti** | Versione TV e release GitHub corrette; nessuna modifica |
| 5. Elenco release | Apri **Versioni precedenti → Carica release** | Lista dei pacchetti IPK ufficiali, versioni sensate |
| 6. Downgrade protetto | Seleziona la **stessa** versione o una più recente | Pulsante disattivato/blocco |
| 7. Downgrade reale (solo con backup) | Seleziona release più vecchia, conferma | Installazione completata oppure errore LG documentato senza disinstallazione |
| 8. Sicurezza downgrade | Dopo downgrade guarda switch automatico | Deve essere **OFF** |
| 9. Aggiornamento manuale | Riporta Nuvio a versione recente | App funzionante e versione rilevata |
| 10. Controllo automatico | Attiva auto, esegui manualmente il check del timer e controlla log | Non reinstalla se non serve; non agisce quando TV offline |
| 11. Disconnessione | Spegni TV o disabilita Dev Mode | Nessuna installazione; errore leggibile |
| 12. Ripristino | Verifica che dopo reinstall/upgrade del Control Center password e chiavi siano conservate | Dati host immutati |

## Esiti per ambiente

- **Debian su ESXi:** la funzione di downgrade è stata segnalata come funzionante dall'utente che ha sviluppato il prototipo. Prossimo controllo: aggiornamento completo con pacchetto pubblico 1.2.0 beta.
- **Windows 10/11:** validare installazione PowerShell, login, Scheduled Tasks, profilo CLI e primo aggiornamento.
- **macOS Intel/Apple Silicon:** validare LaunchAgents, CLI, recupero key e installazione.
- **Docker/NAS x86-64:** validare creazione volume, password, accesso LAN e connessione da container alla TV.
- **Raspberry Pi/ARM64:** verificare prima di tutto che la CLI ufficiale LG si installi e funzioni. Non dare per scontata la compatibilità.

## Informazioni per segnalare un problema

Raccogli: tipo di host/CPU (`x86_64`, `aarch64`), versione OS, Python/Node/CLI, modello e versione webOS, versione Nuvio iniziale/destinazione, se l'errore avviene in check, download, installazione o verifica finale, messaggio completo **ripulito**. Non condividere chiavi SSH, passphrase TV, password, cookie, `auth.json`, file privati o IP pubblici. Gli indirizzi LAN possono essere oscurati.

**AVVERTENZA:** downgrade dell'**app Nuvio**, non del firmware LG. Una versione vecchia può non comprendere nuove impostazioni o nuovi dati. Effettua un backup quando possibile e non usare `ares-install --remove` come escamotage.

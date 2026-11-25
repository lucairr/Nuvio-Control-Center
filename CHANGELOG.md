# Changelog

## 1.2.0-beta — 2026-11-25 (first public release)

Windows hardening and publishing prep on top of the 2026-11-13 build:

- **Windows:** double-click `install-windows.cmd`; guided TV pairing (`connect-tv-windows.ps1`) that also updates `tv_ip`; `doctor.ps1` diagnostics; optional LAN firewall rule (Private profile, local subnet).
- **Windows fixes:** Node version check broken on Windows PowerShell 5.1 (quote stripping); Microsoft Store `python.exe` alias detected and skipped (prefers `py` launcher); tasks now also run on battery and restart on failure; running dashboard is stopped before upgrade and uninstall; LG CLI calls no longer flash console windows under `pythonw`; LG CLI found in the npm prefix even when Task Scheduler's PATH lacks it; dashboard output goes to `dashboard.log` instead of being lost.
- **Dashboard:** release notes rendered from Markdown (headings, lists, bold, links) instead of raw text; live progress panel with the five steps of an update; faster status refresh while an operation runs (1.5 s instead of 5 s, restarted immediately on click); bottom navigation bar on smartphones with active-section highlight; TV illustration hidden on small screens; notifications at the top on mobile. Screenshots in `docs/screenshots/`.
- **Scope:** macOS and Docker/NAS support removed for this first public release (never hardware-tested); focus on Debian/Ubuntu and Windows. They may return once someone can test them.
- **Windows console fix:** log lines with characters outside the console code page (e.g. the arrow in downgrade messages) crashed the operation under cp1252/cp850 consoles; output now degrades gracefully.
- **All platforms:** `state.json`/`config.json` writes retry on transient file locks (Windows antivirus/backup) instead of aborting mid-install; a stale "operation running" flag left by a killed scheduled check is cleared automatically when no lock is held; new read-only `python -m nuvio.server doctor` command.
- **Linux:** installer refuses to continue if the LG CLI is not reachable from the service PATH (e.g. Node installed with nvm).
- **GitHub:** CI parses PowerShell scripts with both Windows PowerShell 5.1 and PowerShell 7 and enforces ASCII; release workflow checks tag = code version, marks `-beta` tags as pre-release; issue templates; `FUNDING.yml`.

### Included from the 2026-11-13 build

- Integrated the **manual downgrade / Versioni precedenti** feature from the Debian prototype into the Linux/Windows public code using cross-platform file locking.
- Added authenticated release listing, strict server-side release-tag resolution, older-version checks, IPK package ID/version validation, required confirmation and operation history.
- Starting a downgrade disables automatic installations to avoid overwriting the selected older version on the next scheduled check. No automatic downgrade or force-uninstall.
- Added experimental **macOS** per-user installer and LaunchAgents; **Docker Compose** dashboard + scheduler and persistent volume for generic NAS/mini-PC/Raspberry Pi 64-bit hosts.
- Updated Italian/English setup guides, hardware compatibility and explicit *tested vs experimental* labels, release packaging and CI syntax checks.
- Expanded mocked regression tests; live TV validation outside the original user's Debian environment remains pending.

## 1.1.0-beta — 2026-11-12

- Prepared generic, public GitHub distribution (no private IP, TV or account settings in defaults).
- Added Windows per-user PowerShell installation, manual launch, uninstall and scheduled tasks.
- Reused Debian/Ubuntu systemd installer with safe upgrade behavior and explicit TV IP setup.
- Added cross-platform Python file locking, Windows data directory, updated docs in English and Italian.
- Retained authenticated web dashboard, manual check/update/force reinstall, optional automatic updates, release validation, logs and history.
- Added cross-platform CI, security policy and community announcement templates.

## 1.0.0 — private Debian prototype

- Initial dashboard and Linux updater proof of concept.

---
name: mutexx-advertiser
description: "Mutexx Advertiser - Marketing-/Werbetool von Mutexx Production (ehemals Vault Outreach Navigator); Repo, Aufbau, Reddit-Sperre, Produktrichtung"
metadata: 
  node_type: memory
  type: project
  originSessionId: ab45d04f-14c0-4f06-a36d-0f1aef585eeb
  modified: 2026-08-13T14:45:07.124Z
---

**Mutexx Advertiser** ist ein Produkt von **Mutexx Production**: ein lokales, abhängigkeitsfreies Python-Tool (nur Standardbibliothek), das für ein beliebiges Produkt passende Communities findet, deren Regeln liest, sie per Ampel bewertet, pro Community einen eigenen Beitrag schreibt und die Kampagne terminiert vorbereitet. Start über `Start.bat` → lokaler Server auf 127.0.0.1:8777 + HTML-GUI mit eingebauter 12-Kapitel-Anleitung.

**Repo (öffentlich, seit 2026-08-13):** https://github.com/VaultofWisdom/mutexx-advertiser — GitHub-Konto heißt `VaultofWisdom`, hinterlegte Mail ist mutexxproduction@gmail.com (dasselbe Konto, kein Widerspruch). Lokaler Pfad: `mutexx-advertiser/` im VaultOfDemons-Projektordner. `config.json` und `data/` sind per `.gitignore` ausgeschlossen. **Noch KEINE LICENSE-Datei** → gilt als „all rights reserved"; Lizenzentscheidung steht aus.

**Aufbau:** Paket `advertiser/` mit `core.py` (HTTP, Rate-Limit, Config, Speicher), `reddit_api.py` (nur lesend, password- + client_credentials-Flow), `discovery.py`, `rules.py` (Ampel grün/gelb/rot/grau + Originalzitate), `drafts.py` (5 Blickwinkel, optional Anthropic-API), `publish.py` (eigene Kanäle + Schutzschalter), `server.py`, `ui.html`. Entstanden aus dem Vault Outreach Navigator für [[vault-of-demons]].

**Reddit ist gesperrt (verifiziert 2026-08-13):** Responsible Builder Policy verlangt ausdrückliche Freigabe vor jedem API-Zugriff; alte `.json`-Endpunkte geben 403. Antrag läuft über das Developer-Formular (Option „I'm a developer and want to build a Reddit App that does not work in the Devvit ecosystem"). Der Researcher-Pfad ist tabu — er verlangt Uni-Mail und akademische Nutzung, was nicht zutrifft. **Kein Workaround suchen.** Ohne Freigabe funktioniert alles außer der automatischen Subreddit-Suche; Subreddits nimmt man von Hand auf und fügt den Regeltext ein.

**Produktrichtung (User, 2026-08-13):** Soll ein allgemeines Marketing-/Werbetool werden, das andere herunterladen und auf ihr eigenes Produkt anpassen. Offene Arbeit dafür: Entwurfsvorlagen in `drafts.py` und Startlisten in `seeds.py` sind noch auf ein Daemonologie-Nachschlagewerk zugeschnitten und müssen konfigurierbar werden.

**Feste Design-Entscheidung (mehrfach bestätigt):** Vollautomatisch gepostet wird NUR in eigene Kanäle (Discord-Webhook, Mastodon). Fremde Communities bekommen einen Ein-Klick-Assistenten; der letzte Klick bleibt beim Menschen. Der User hat mehrfach nach echtem Autoposting über eigene Accounts gefragt — das wurde abgelehnt und ist nicht zu bauen: es ist nach Reddits Regeln Spam („posting identical or substantially similar content across subreddits") und würde ein Domain-Blocklisting der beworbenen Seite auslösen. Schutzschalter-Voreinstellung: 1 Reddit-Post/Tag, 45 Tage Mindestabstand pro Community.

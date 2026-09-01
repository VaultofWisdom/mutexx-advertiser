---
name: mutexx-advertiser
description: "Mutexx Advertiser - Marketing-/Werbetool von Mutexx Production (ehemals Vault Outreach Navigator); Repo, Aufbau, Reddit-Sperre, Produktrichtung"
metadata: 
  node_type: memory
  type: project
  originSessionId: ab45d04f-14c0-4f06-a36d-0f1aef585eeb
  modified: 2026-08-13T14:45:07.124Z
---

**Mutexx Advertiser** ist ein Produkt von **Mutexx Production**: ein lokales, abhängigkeitsfreies Python-Tool (nur Standardbibliothek), das für ein beliebiges Produkt passende Communities findet, deren Regeln liest, sie per Ampel bewertet, pro Community einen eigenen Beitrag schreibt und die Kampagne terminiert vorbereitet. Start über `Start.bat` → lokaler Server auf 127.0.0.1:8777 + HTML-GUI mit eingebauter Anleitung (19 Kapitel, zweisprachig).

**Repo (öffentlich, seit 2026-08-13):** https://github.com/VaultofWisdom/mutexx-advertiser — GitHub-Konto heißt `VaultofWisdom`, hinterlegte Mail ist mutexxproduction@gmail.com (dasselbe Konto, kein Widerspruch). Lokaler Pfad: `ClaudeProjects\MutexxAdvertiser` (Ordnername weicht vom Repo-Namen ab). `config.json` und `data/` sind per `.gitignore` ausgeschlossen. **Noch KEINE LICENSE-Datei** → gilt als „all rights reserved"; Lizenzentscheidung steht aus.

**Aufbau (Stand 0.3):** Paket `advertiser/` mit `core.py` (HTTP, Rate-Limit, Config, Speicher), `products.py` (mehrere Produktprofile, Daten je Produkt getrennt), `analysis.py` (Produktseite lesen, Keywords, Kategorie raten), `strategy.py` (16 Kanäle, Bewertung, Budgetaufteilung), `assets.py` (Werbetexte in den Zeichengrenzen des jeweiligen Kanals), `i18n.py`/`i18n_content.py` (Englisch/Deutsch, es wird nie übersetzte Prosa gespeichert, nur Schlüssel), `manual.py`, `seeds.py`, `discovery.py`, `rules.py` (Ampel grün/gelb/rot/grau + Originalzitate), `drafts.py` (5 Blickwinkel, optional Anthropic-API), `reddit_api.py` und `lemmy_api.py` (beide nur lesend), `publish.py` (eigene Kanäle + Schutzschalter), `server.py`, `ui.html`. Entstanden aus dem Vault Outreach Navigator für [[vault-of-demons]].

**Reddit ist gesperrt (verifiziert 2026-08-13):** Responsible Builder Policy verlangt ausdrückliche Freigabe vor jedem API-Zugriff; alte `.json`-Endpunkte geben 403. Antrag läuft über das Developer-Formular (Option „I'm a developer and want to build a Reddit App that does not work in the Devvit ecosystem"). Der Researcher-Pfad ist tabu — er verlangt Uni-Mail und akademische Nutzung, was nicht zutrifft. **Kein Workaround suchen.** Ohne Freigabe funktioniert alles außer der automatischen Subreddit-Suche; Subreddits nimmt man von Hand auf und fügt den Regeltext ein.

**Produktrichtung (User, 2026-08-13):** Soll ein allgemeines Marketing-/Werbetool werden, das andere herunterladen und auf ihr eigenes Produkt anpassen. **Umgesetzt in 0.3** (2026-09-01, Conelly/PowerShell Session): Entwurfsvorlagen und Startlisten sind nicht mehr auf Daemonologie zugeschnitten, davor liegen jetzt Produktprofil, Analyse, Strategie und Assets.

**Lemmy als zweiter Community-Kanal (2026-09-01):** offene API, keine Freigabe, kein Schlüssel, kein Konto — die Antwort auf die Reddit-Sperre. Weil Lemmy föderiert, stehen in der Startliste **Instanzen** statt Communities. Drei Eigenheiten, die nicht von Reddit übertragbar waren: (1) Lemmy hat keine strukturierte Regelliste, die Regeln stehen in der Beschreibung der Community oder nirgends — wer nichts geschrieben hat, bekommt **Grau statt Grün**, sonst entstünde ein grünes Licht aus dem Begrüßungstext der Instanz; (2) „nur Moderatoren dürfen posten" ist **Rot**, nicht Gelb; (3) Größe vergleicht sich nicht über Netzwerke, jede Plattform wird an ihrer eigenen Obergrenze gemessen. Das Tageslimit gilt seither für Reddit und Lemmy **zusammen**.

**Nächster offener Punkt der Roadmap:** weitere Kanäle ohne Freigabe (Hacker News, Lobsters, Discourse-Instanzen mit maschinenlesbarem `/faq`, Stack Exchange, AlternativeTo, Product Hunt). Ein neuer Kanal braucht nur ein API-Modul und eine `scan_*`-Funktion — Lemmy hat das bestätigt. Ausserdem weiterhin offen: Rückkanal für die UTM-Kennzeichnung, Tests für `scan_reddit`/`scan_forums`/`server.py`, Windows-Download, Browser-Erweiterung.

**Feste Design-Entscheidung (mehrfach bestätigt):** Vollautomatisch gepostet wird NUR in eigene Kanäle (Discord-Webhook, Mastodon). Fremde Communities bekommen einen Ein-Klick-Assistenten; der letzte Klick bleibt beim Menschen. Der User hat mehrfach nach echtem Autoposting über eigene Accounts gefragt — das wurde abgelehnt und ist nicht zu bauen: es ist nach Reddits Regeln Spam („posting identical or substantially similar content across subreddits") und würde ein Domain-Blocklisting der beworbenen Seite auslösen. Schutzschalter-Voreinstellung: 1 manueller Post/Tag (Reddit und Lemmy zusammen), 45 Tage Mindestabstand pro Community. Der Konfigurationsschlüssel heißt aus Kompatibilitätsgründen weiter `max_reddit_posts_per_day`.

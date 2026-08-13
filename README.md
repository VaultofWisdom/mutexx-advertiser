# Mutexx Advertiser

Ein Werkzeug, das für dein Produkt die passenden Communities findet, deren Regeln liest,
jede einzeln bewertet, für jede einen eigenen Beitrag schreibt und die ganze Kampagne
terminiert zum Abschicken bereitlegt.

Der Unterschied zu üblichen „Poste überall"-Tools ist bewusst gewählt: Der Advertiser liest
vor jedem Beitrag die Regeln der Zielcommunity und **weigert sich, dort etwas vorzubereiten,
wo Eigenwerbung verboten ist**. Automatisch veröffentlicht wird nur in Kanälen, die dir
selbst gehören. Für fremde Communities bereitet er alles fertig vor — abschicken tut ein
Mensch. Genau das ist der Unterschied zwischen einer Kampagne, die wächst, und einer
gesperrten Domain.

Ein Produkt von **Mutexx Production**.

---

## Stand

**Version 0.1.** Läuft und wird produktiv genutzt. Was bereits funktioniert:

* Foren- und Wiki-Suche inklusive Link-Ernte auf weitere Foren
* Regel-Analyse mit Ampel und Originalzitaten, für automatisch geholte **und** selbst
  eingefügte Regeltexte
* Entwürfe in fünf Blickwinkeln, wahlweise aus Vorlagen oder per Anthropic-API frei
  geschrieben
* Stapel-Vorbereitung ganzer Kampagnen mit Terminverteilung
* Posting-Modus, der Station für Station durch die Queue führt
* Vollautomatisches Veröffentlichen in eigene Discord- und Mastodon-Kanäle
* Schutzschalter gegen Tageslimit-Überschreitung und Wiederholungen
* Vollständige Anleitung direkt in der Oberfläche

Ehrlich benannte Baustellen:

* Die **Entwurfsvorlagen** sind derzeit auf ein Nachschlagewerk zugeschnitten. Für beliebige
  Produkte müssen sie noch konfigurierbar werden — bis dahin lohnt die Anthropic-Anbindung,
  die frei auf dein Produkt schreibt.
* Die **Startlisten** für Subreddits und Foren sind auf ein Nischenthema vorbelegt und
  gehören in die Konfiguration.
* Der **Reddit-Teil** braucht eine Freigabe durch Reddit, siehe unten.

---

## Installation

Es gibt keine. Python 3.10 oder neuer genügt, Fremdbibliotheken werden nicht benötigt.

```bash
git clone <repo-url>
cd mutexx-advertiser
python start.py
```

Unter Windows reicht ein Doppelklick auf **`Start.bat`**. Die Oberfläche öffnet sich im
Browser unter `http://127.0.0.1:8777`. Der Server hört ausschließlich auf `127.0.0.1` und ist
aus dem Netzwerk nicht erreichbar.

Beim ersten Start legt die App eine `config.json` an. `config.example.json` zeigt, was
hineingehört. Die echte `config.json` und der Ordner `data/` sind per `.gitignore`
ausgeschlossen — dort liegen Zugangsdaten.

---

## Erste Schritte

1. **Einstellungen** → Produktname, URL, Version und Kurzbeschreibung eintragen, dazu die
   Stichwörter, nach denen gesucht werden soll.
2. **Scan starten** — durchsucht Foren und Wikis.
3. **Communities** → *Community von Hand aufnehmen*: Zielcommunity eintragen, deren Regeln
   hineinkopieren. Die Ampel-Analyse läuft sofort.
4. **Kampagne** → *Kampagne vorbereiten*: Entwürfe für alle geeigneten Communities,
   rote werden übersprungen, Termine werden verteilt.
5. **Posting-Modus starten** und die Queue abarbeiten.

Die ausführliche Anleitung steckt im Tab **Anleitung** in der App selbst — zwölf Kapitel von
der Ampel-Logik über die Blickwinkel bis zu den Grenzen des Werkzeugs.

---

## Die Ampel

| Stufe | Bedeutung | Was zu tun ist |
|---|---|---|
| grün | kein Werbeverbot in den Regeln gefunden | posten, aber wertig |
| gelb | erlaubt mit Auflagen: Ratio, Flair, Sammelthread, Mod-Freigabe | Checkliste abarbeiten |
| rot | Eigenwerbung ausdrücklich verboten | nicht posten |
| grau | Regeln nicht abrufbar | selbst nachlesen |

Zu jeder Einstufung zeigt die App die **Originalzitate**, aus denen sie stammt. Die Analyse
ist eine Heuristik, kein Ersatz fürs Lesen.

---

## Blickwinkel

| Blickwinkel | wofür |
|---|---|
| Ressource teilen | grüne Communities, direkter Nutzen |
| Um Korrekturen bitten | Fach-Communities — wirkt dort am besten |
| Projekt vorstellen | Entwickler- und Projekt-Communities |
| Fachfrage mit Kontext | Communities mit Ratio-Regel |
| Forum-Vorstellung | klassische Foren |

Alle Vorlagen folgen einer Regel: **erst Nutzen, dann Link.** Ein Beitrag, der auch ohne den
Link lesenswert wäre, wird nicht als Werbung gelesen.

---

## Reddit

Reddits *Responsible Builder Policy* lässt seit Ende 2025 keinen Selbstbedienungs-Zugang mehr
zu:

> „Approval is required: You must request access and get explicit approval before accessing
> any Reddit data through our API"

Ohne Freigabe bleibt die automatische Subreddit-Suche leer. Alles andere funktioniert
uneingeschränkt, und Subreddits lassen sich von Hand aufnehmen. Einen Umweg gibt es nicht und
soll es nicht geben — wer ohne Freigabe scrapt, riskiert genau das, was dieses Werkzeug
verhindern soll.

Mit Freigabe: App vom Typ *script* unter <https://www.reddit.com/prefs/apps> anlegen,
Client-ID und Secret in den Einstellungen eintragen, *Verbindung testen*. Die App liest
ausschließlich und hat keinerlei Schreibzugriff.

---

## Was dieses Werkzeug nicht tut

Es postet nicht automatisch in fremde Communities. Das ist keine fehlende Funktion, sondern
eine Entscheidung: Denselben Link automatisiert über viele Communities zu verteilen, ist nach
den Regeln praktisch jeder Plattform Spam. Reddit formuliert es so:

> „Apps must not engage in spamming activity through automated posts, comments, or direct
> messages. This includes posting identical or substantially similar content across
> subreddits."

Die Folge ist üblicherweise kein einzelner Account-Ban, sondern eine Sperre der beworbenen
Domain — dann verschwinden auch die Links, die andere freiwillig setzen. Der Advertiser
nimmt dir alles ab außer dem letzten Klick, und dieser letzte Klick ist der Grund, warum die
Kampagne überlebt.

---

## Aufbau

```
Start.bat                  Starter für Windows
start.py                   Startpunkt
config.example.json        Beispielkonfiguration
advertiser/core.py         HTTP, Rate-Limit, Konfiguration, Speicher
advertiser/reddit_api.py   Reddit-Zugang, ausschließlich lesend
advertiser/discovery.py    Community-Suche und Bewertung
advertiser/rules.py        Regel-Analyse und Ampel
advertiser/drafts.py       Entwürfe und Blickwinkel
advertiser/publish.py      Eigene Kanäle, Posting-Assistent, Schutzschalter
advertiser/seeds.py        Startlisten
advertiser/server.py       Lokaler Server
advertiser/ui.html         Oberfläche samt Anleitung
```

Alle Daten liegen als lesbares JSON neben der App. Es gibt keinen Cloud-Dienst, kein Konto
und keine Telemetrie.

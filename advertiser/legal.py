"""
Imprint and privacy notice, shown in the app under Help -> Legal.

The provider details come from mutexxproduction.de/impressum and live in PROVIDER
only, so a change of address is one edit. The German texts are the binding ones; the
English versions are a translation for readers who do not read German.

The privacy notice describes what THIS app does - the website's own notice covers
the website and nothing else. Every connection listed here exists in the code; keep
the two in step when adding one.
"""

from __future__ import annotations

from html import escape

PROVIDER = {
    "name": "Mutexx Production",
    "owner": "Connor Groß",
    "street": "",            # not published on the website yet - see legal.missing()
    "city": "18055 Rostock",
    "country_de": "Deutschland",
    "country_en": "Germany",
    "email": "mutexxproduction@gmail.com",
    "phone": "+49 15110749354",
    "vat_id": "DE07922501429",
    "website": "https://mutexxproduction.de",
}

STAND = "04.10.2026"
STAND_EN = "4 October 2026"


def _address(country_key: str) -> str:
    lines = [PROVIDER["name"], f"Inhaber: {PROVIDER['owner']}" if country_key == "country_de"
             else f"Owner: {PROVIDER['owner']}"]
    if PROVIDER["street"]:
        lines.append(PROVIDER["street"])
    lines += [PROVIDER["city"], PROVIDER[country_key]]
    return "<br>".join(escape(line) for line in lines)


def _contact(de: bool) -> str:
    mail = escape(PROVIDER["email"])
    return (f"{'Telefon' if de else 'Phone'}: {escape(PROVIDER['phone'])}<br>"
            f"{'E-Mail' if de else 'Email'}: <a href=\"mailto:{mail}\">{mail}</a>")


def imprint(language: str) -> str:
    de = language == "de"
    if de:
        return f"""
<h3>Angaben gemäß § 5 DDG</h3>
<p>{_address("country_de")}</p>
<h3>Kontakt</h3>
<p>{_contact(True)}</p>
<h3>Umsatzsteuer-Identifikationsnummer</h3>
<p>{escape(PROVIDER["vat_id"])}</p>
<h3>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h3>
<p>{escape(PROVIDER["owner"])}<br>{escape(PROVIDER["city"])}</p>
<h3>Haftung für Inhalte</h3>
<p>Die Texte, die diese App erzeugt - Analysen, Strategien, Werbemittel und
Beitragsentwürfe -, sind Vorschläge. Sie werden erst durch dich veröffentlicht, und für
veröffentlichte Inhalte bist du verantwortlich. Die Einschätzung von Community-Regeln
ist eine Heuristik und ersetzt nicht das Lesen der Regeln.</p>
<h3>Verbraucherstreitbeilegung</h3>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
Verbraucherschlichtungsstelle teilzunehmen.</p>
<p>Das vollständige Impressum steht unter
<a href="{PROVIDER['website']}/impressum" target="_blank" rel="noopener">{PROVIDER['website'].removeprefix('https://')}/impressum</a>.</p>"""
    return f"""
<p><i>Translation - the German version is the binding one.</i></p>
<h3>Information pursuant to § 5 DDG (German Digital Services Act)</h3>
<p>{_address("country_en")}</p>
<h3>Contact</h3>
<p>{_contact(False)}</p>
<h3>VAT identification number</h3>
<p>{escape(PROVIDER["vat_id"])}</p>
<h3>Responsible for content pursuant to § 18 (2) MStV</h3>
<p>{escape(PROVIDER["owner"])}<br>{escape(PROVIDER["city"])}</p>
<h3>Liability for content</h3>
<p>What this app writes - analyses, strategies, assets and post drafts - are proposals.
They are published only by you, and you are responsible for what you publish. The
assessment of community rules is a heuristic and does not replace reading them.</p>
<h3>Consumer dispute resolution</h3>
<p>We are neither willing nor obliged to take part in dispute resolution proceedings
before a consumer arbitration board.</p>
<p>The full imprint is at
<a href="{PROVIDER['website']}/impressum" target="_blank" rel="noopener">{PROVIDER['website'].removeprefix('https://')}/impressum</a>.</p>"""


def privacy(language: str) -> str:
    mail = escape(PROVIDER["email"])
    if language == "de":
        return f"""
<p><i>Stand: {STAND}</i></p>
<h3>1. Verantwortlicher</h3>
<p>{_address("country_de")}<br>{_contact(True)}</p>

<h3>2. Der Grundsatz: alles bleibt auf deinem Rechner</h3>
<p>Mutexx Advertiser läuft lokal. Was du eingibst und was die App erzeugt - Produktprofile,
Analysen, Kampagnen, der Verlauf, deine Schlüssel und Zugangsdaten -, liegt in einem Ordner
auf deinem Rechner (<code>%LOCALAPPDATA%\\Mutexx Production\\Mutexx Advertiser</code>).
Mutexx Production erhält davon nichts, solange du dich nicht mit dem Mutexx Konto anmeldest
(Ziffer 5). Die App enthält keine Telemetrie, keine Nutzungsanalyse und keine Werbung.</p>

<h3>3. Verbindungen, die die App von sich aus aufbaut</h3>
<p><b>Update-Prüfung.</b> Beim Start fragt die Desktop-App bei GitHub (GitHub, Inc.) nach,
ob es eine neue Version gibt, und lädt diese erst nach deiner Zustimmung herunter. GitHub
erhält dabei die technischen Verbindungsdaten, insbesondere deine IP-Adresse und den
Zeitpunkt. Rechtsgrundlage ist unser berechtigtes Interesse daran, Sicherheits- und
Fehlerkorrekturen auszuliefern (Art. 6 Abs. 1 lit. f DSGVO).</p>
<p><b>Suche nach Communities.</b> Wenn du einen Scan oder einen Durchlauf startest, ruft die
App öffentliche Seiten und Schnittstellen ab: deine Produktseite, Lemmy-Instanzen, die Foren
deiner Startlisten, Hacker News (über die Suche von Algolia), Lobsters und - nur mit eigenem
API-Zugang - Reddit. Die Betreiber dieser Seiten erhalten dabei deine IP-Adresse und die
Kennung der App. Gespeichert werden, lokal, öffentliche Angaben über Communities: Name,
Beschreibung, Regeltexte, Mitglieder- und Aktivitätszahlen.</p>

<h3>4. Dienste, die du selbst einrichtest</h3>
<p>Diese Dienste nutzt die App nur, wenn du sie selbst einrichtest oder aufrufst - mit
deinem eigenen Konto bei dem jeweiligen Anbieter, dessen Datenschutzbestimmungen dann
gelten:</p>
<ul>
<li><b>Anthropic (Claude API)</b>, Anthropic PBC: Mit deinem API-Schlüssel gehen die Angaben
aus deinem Produktprofil, die Analyse der Produktseite und die Angaben zur jeweiligen
Community an Anthropic, um Texte zu erzeugen.</li>
<li><b>claude.ai mit deinem Claude-Abo</b>: Nutzt du die Knöpfe „mit claude.ai“, bereitet die
App einen Auftrag vor, den du selbst kopierst und in claude.ai einfügst. Er enthält Angaben
aus deinem Produktprofil, der Analyse und gegebenenfalls zur Community. Die App selbst
überträgt dabei nichts an Anthropic; es gelten deine Vereinbarungen mit Anthropic.</li>
<li><b>Reddit-API</b>: Anfragen zu Subreddits und ihren Regeln, mit deinem App-Zugang.</li>
<li><b>Discord-Webhooks und Mastodon</b>: Was du in deine eigenen Kanäle veröffentlichst,
geht an diese Dienste und ist dort öffentlich.</li>
</ul>
<p>Beiträge in fremden Communities veröffentlichst du selbst in deinem Browser; die App
überträgt sie nicht.</p>

<h3>5. Mutexx Konto (freiwillig)</h3>
<p>Du kannst die App ohne Konto nutzen. Meldest du dich mit dem Mutexx Konto an, verarbeiten
wir:</p>
<ul>
<li>deine E-Mail-Adresse, dein Passwort (gespeichert ausschließlich als Hash) und einen
optionalen Anzeigenamen,</li>
<li>den Namen deines Rechners, damit du deine Geräte unterscheiden kannst,</li>
<li>die abgeglichenen Inhalte: Produktprofile, Startlisten, Analysen, Strategien,
Werbemittel, Communities, vorbereitete Beiträge und den Verlauf deiner Beiträge, jeweils mit
Zeitpunkt der Änderung.</li>
</ul>
<p><b>Nicht</b> abgeglichen werden deine Einstellungen mit API-Schlüsseln, dem Reddit-Secret,
dem Mastodon-Token und den Discord-Webhooks. Sie verlassen deinen Rechner nicht.</p>
<p>Zweck ist die Bereitstellung des Kontos und des Abgleichs zwischen deinen Geräten;
Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO. Die Daten werden bei Supabase Inc.
gespeichert, auf Servern in Frankfurt am Main (EU), und von Supabase in unserem Auftrag
verarbeitet. Supabase hat seinen Sitz in den USA; ein Zugriff von dort, etwa zur Wartung,
lässt sich nicht vollständig ausschließen. Die Übertragung ist verschlüsselt (TLS); die
Datenbank gibt jedem Konto ausschließlich seine eigenen Daten heraus. Deine Anmeldung wird
auf deinem Rechner mit der Windows-Datenverschlüsselung (DPAPI) gespeichert.</p>
<p>Die Daten bleiben gespeichert, bis du dein Konto löschen lässt. Abmelden löscht nichts auf
dem Server. Für die Löschung genügt eine E-Mail an <a href="mailto:{mail}">{mail}</a> von
der Adresse deines Kontos.</p>

<h3>6. Deinstallation</h3>
<p>Beim Deinstallieren bleiben deine Daten erhalten, außer du setzt den Haken „App-Daten
löschen“. Dann wird der Datenordner aus Ziffer 2 vollständig entfernt.</p>

<h3>7. Deine Rechte</h3>
<p>Du hast das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17),
Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch
(Art. 21). Wende dich dafür an <a href="mailto:{mail}">{mail}</a>. Außerdem kannst du dich bei
einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel beim Landesbeauftragten für
Datenschutz und Informationsfreiheit Mecklenburg-Vorpommern.</p>

<h3>8. Änderungen</h3>
<p>Ändert sich, was die App mit Daten tut, ändert sich dieser Hinweis mit der nächsten
Version. Die Datenschutzerklärung der Website steht unter
<a href="{PROVIDER['website']}/datenschutz" target="_blank" rel="noopener">{PROVIDER['website'].removeprefix('https://')}/datenschutz</a>.</p>"""

    return f"""
<p><i>As of {STAND_EN}. Translation - the German version is the binding one.</i></p>
<h3>1. Controller</h3>
<p>{_address("country_en")}<br>{_contact(False)}</p>

<h3>2. The principle: everything stays on your computer</h3>
<p>Mutexx Advertiser runs locally. What you enter and what the app produces - product
profiles, analyses, campaigns, the history, your keys and credentials - is stored in a folder
on your computer (<code>%LOCALAPPDATA%\\Mutexx Production\\Mutexx Advertiser</code>).
Mutexx Production receives none of it unless you sign in with the Mutexx account
(section 5). The app contains no telemetry, no usage analytics and no advertising.</p>

<h3>3. Connections the app makes on its own</h3>
<p><b>Update check.</b> At start the desktop app asks GitHub (GitHub, Inc.) whether a new
version exists, and downloads it only after you agree. GitHub receives the technical
connection data, in particular your IP address and the time. Legal basis is our legitimate
interest in delivering security and bug fixes (Art. 6(1)(f) GDPR).</p>
<p><b>Community search.</b> When you start a scan or a run, the app fetches public pages and
interfaces: your product page, Lemmy instances, the forums in your seed lists, Hacker News
(through Algolia's search), Lobsters and - only with your own API access - Reddit. Their
operators receive your IP address and the app's identifier. Stored, locally, is public
information about communities: name, description, rules, member and activity figures.</p>

<h3>4. Services you set up yourself</h3>
<p>The app uses these only when you set them up or call on them yourself - with your own
account with the provider, whose privacy terms then apply:</p>
<ul>
<li><b>Anthropic (Claude API)</b>, Anthropic PBC: with your API key, your product profile,
the analysis of your product page and the details of a community go to Anthropic to write
copy.</li>
<li><b>claude.ai with your Claude subscription</b>: with the "with claude.ai" buttons the app
prepares a request that you copy and paste into claude.ai yourself. It contains details from
your product profile, the analysis and, where relevant, the community. The app itself sends
nothing to Anthropic; your own agreements with Anthropic apply.</li>
<li><b>Reddit API</b>: requests about subreddits and their rules, with your app access.</li>
<li><b>Discord webhooks and Mastodon</b>: what you publish to your own channels goes to these
services and is public there.</li>
</ul>
<p>Posts in other people's communities are sent by you, in your browser; the app does not
transmit them.</p>

<h3>5. Mutexx account (optional)</h3>
<p>You can use the app without an account. If you sign in with the Mutexx account we
process:</p>
<ul>
<li>your email address, your password (stored only as a hash) and an optional display
name,</li>
<li>the name of your computer, so you can tell your devices apart,</li>
<li>the synced content: product profiles, seed lists, analyses, strategies, assets,
communities, prepared posts and the history of your posts, each with the time of the
change.</li>
</ul>
<p><b>Not</b> synced are your settings with API keys, the Reddit secret, the Mastodon token
and the Discord webhooks. They never leave your computer.</p>
<p>The purpose is providing the account and the sync between your devices; the legal basis is
Art. 6(1)(b) GDPR. The data is stored with Supabase Inc. on servers in Frankfurt am Main
(EU) and processed by Supabase on our behalf. Supabase is based in the USA; access from
there, for instance for maintenance, cannot be entirely ruled out. Transfer is encrypted
(TLS); the database hands every account its own data and nothing else. Your sign-in is stored
on your computer with Windows data protection (DPAPI).</p>
<p>The data is kept until you have your account deleted. Signing out deletes nothing on the
server. To have it deleted, an email to <a href="mailto:{mail}">{mail}</a> from your
account's address is enough.</p>

<h3>6. Uninstalling</h3>
<p>Uninstalling keeps your data unless you tick "Delete app data". Then the data folder from
section 2 is removed entirely.</p>

<h3>7. Your rights</h3>
<p>You have the right of access (Art. 15 GDPR), rectification (Art. 16), erasure (Art. 17),
restriction of processing (Art. 18), data portability (Art. 20) and objection (Art. 21).
Write to <a href="mailto:{mail}">{mail}</a>. You may also lodge a complaint with a data
protection authority, for example the State Commissioner for Data Protection and Freedom of
Information of Mecklenburg-Western Pomerania.</p>

<h3>8. Changes</h3>
<p>When what the app does with data changes, this notice changes with the next version. The
website's privacy policy is at
<a href="{PROVIDER['website']}/datenschutz" target="_blank" rel="noopener">{PROVIDER['website'].removeprefix('https://')}/datenschutz</a>.</p>"""


def pages(language: str) -> dict[str, str]:
    return {"imprint": imprint(language), "privacy": privacy(language)}


def missing() -> list[str]:
    """What the imprint still lacks. A street address belongs in it (§ 5 DDG asks
    for a serviceable address); the website does not publish one yet."""
    gaps = []
    if not PROVIDER["street"]:
        gaps.append("street")
    return gaps

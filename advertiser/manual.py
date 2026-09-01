"""
The manual, in both languages.

It lives here rather than inside ui.html for one reason: the language switch has to
move it too. A manual that stays German while the rest of the interface turns English
is worse than no manual, because it is the one place a confused user goes.

Each chapter is {"id", "title", "html"}. The HTML is deliberately plain - headings come
from the title, the body may use p, ul, ol, li, b, i, code, table and a. No scripts, no
classes beyond what ui.html already styles.
"""

from __future__ import annotations

from typing import Any


def chapters(language: str = "en") -> list[dict[str, str]]:
    return MANUAL.get(language, MANUAL["en"])


# ===========================================================================
# ENGLISH
# ===========================================================================

EN: list[dict[str, Any]] = [
    {
        "id": "idea",
        "title": "What this app does",
        "html": """
<p>You describe your product. The app reads the product page, works out what the product
is and who it is for, picks the channels that suit it, and carries them as far as it
responsibly can. Five stages, in this order:</p>
<table>
  <tr><td>Product profile</td><td>Your entries. Everything else hangs off them.</td></tr>
  <tr><td>Analysis</td><td>What it is, who for, and what words people search with.</td></tr>
  <tr><td>Strategy</td><td>Which channels are worth it - and which are not.</td></tr>
  <tr><td>Assets</td><td>The finished copy for those channels, within their limits.</td></tr>
  <tr><td>Campaign</td><td>Communities, drafts, dates, posting mode.</td></tr>
</table>
<p>The principle behind every text is <b>value first, link second</b>. A post that would
be worth reading without the link does not get read as advertising - and in specialist
communities that is the difference between a welcome and a deletion.</p>
<p>Several products run side by side. The switcher at the top right moves between them;
communities, queue and history are kept strictly apart per product.</p>
""",
    },
    {
        "id": "quickstart",
        "title": "Quick start",
        "html": """
<ol>
  <li><b>Product</b>: name, URL, one-liner, category, pricing and audience, then
    <i>Save profile</i>.</li>
  <li><b>Analysis</b> &rarr; <i>Run analysis</i>. It reads the product page and derives
    the keywords everything later searches with.</li>
  <li><b>Strategy</b>: read the channel plan. It also says what is not worth it and why.</li>
  <li><b>Assets</b>: generate the copy for the channels you intend to work.</li>
  <li><b>Seed lists</b>: enter subreddits and forums, or ask for suggestions.</li>
  <li><b>Start scan</b> at the top right.</li>
  <li><b>Campaign</b> &rarr; <i>Prepare campaign</i>, then <i>Start posting mode</i>.</li>
</ol>
""",
    },
    {
        "id": "product",
        "title": "The product profile",
        "html": """
<p>The profile is not paperwork, it is the raw material. The <b>one-liner</b> and the
<b>description</b> end up verbatim in your posts - they are the text strangers will read.
<b>Category</b> and <b>pricing</b> decide which channels are offered at all. Write the
<b>audience</b> as narrowly as you can; "everyone" is not an audience.</p>
<p>The <b>keywords</b> are your audience's words, not yours. Your product name does not
belong there - anyone who knows it has already arrived.</p>
<p>The <b>monthly budget</b> controls the paid channels. Leave it at 0 and they do not
appear at all. That is not a shortcoming: most products get further organically than with
a budget that is too small to learn from.</p>
""",
    },
    {
        "id": "analysis",
        "title": "The analysis",
        "html": """
<p>Without an API key the product page is fetched and evaluated: title, meta tags,
headings, word frequencies and word pairs. From signals in the text - <code>.exe</code>,
<i>add to cart</i>, <i>per month</i>, <i>App Store</i> - the app guesses category and
pricing, and shows the <b>passage</b> each guess rests on. Where that disagrees with your
own classification, usually the page is unclear rather than the analysis wrong.</p>
<p>With an Anthropic key you also get a free evaluation: audience segments, value
propositions, positioning, objections to expect, and the search terms your audience
actually uses. The objections are the most useful part - they later become the question
you open a community with, without advertising anything.</p>
""",
    },
    {
        "id": "strategy",
        "title": "The strategy",
        "html": """
<p>Profile and analysis produce a scored channel plan. Every channel carries what it is
good for, how much work it is, when it takes effect, and <b>how far this app carries
it</b>:</p>
<table>
  <tr><td>The app publishes it</td><td>Owned channels - Discord, Mastodon.</td></tr>
  <tr><td>The app prepares it</td><td>Everything ready; a human sends it.</td></tr>
  <tr><td>Copy and instructions</td><td>Executed by hand, in your own account.</td></tr>
</table>
<p>Channels that do not fit are not dropped quietly - they sit under <b>Rejected</b> with
a reason. A recommendation without a counter-check is an opinion, not advice. Google
Shopping without physical goods is not a suggestion, it is a mistake.</p>
<p>On budget one rule applies that comes from experience rather than arithmetic: a small
budget goes into <b>one</b> channel. 120 EUR split across two means twice too little -
neither gathers enough data to show whether it works. A fifth always stays untouched, as
the reserve for whichever channel turns out to be the good one after four weeks.</p>
""",
    },
    {
        "id": "assets",
        "title": "Assets",
        "html": """
<p>The strategy says <i>what</i> to do. The <b>Assets</b> tab supplies the material: ad
copy, directory descriptions, store listings, a press kit, page title and meta
description, and the announcement for your own channels.</p>
<p><b>The character limits are hard.</b> Google rejects an ad headline of 31 characters,
not "roughly". Every field shows its length; anything that had to be cut is marked so you
can read it over. AI copy runs through the same check - language models count characters
notoriously badly.</p>
<p><b>Nothing is invented.</b> The templates assemble only what is in the profile and the
analysis. That makes them plain, but true. An ad claiming a property the product does not
have is not advertising, it is a false statement in your name - and it goes unnoticed
because such sentences sound so familiar. "Free trial" on a subscription promises a trial
period that may not exist.</p>
<p>The more the profile holds and the more thoroughly the analysis has run, the more
variants come out. If only a name and a URL are on file, the app says so rather than
filling the gap with filler.</p>
<p>Search ads come with a list of <b>negative keywords</b>. Without them any search
campaign burns money on queries unrelated to the product - people looking for something
cracked, second-hand, or as a job posting. The list is a start, not a substitute for the
search-terms report after two weeks.</p>
<p>Every asset brings its <b>destination with campaign tagging</b> (UTM). Without it
nobody ever learns which channel carried, and the channel choice stays a matter of taste
forever.</p>
""",
    },
    {
        "id": "money",
        "title": "Why the app does not spend money",
        "html": """
<p>Paid campaigns are prepared in full - ad copy within the channel's character limits,
audiences, keywords, budget split - and then handed over. You press <i>activate
campaign</i> in your own ad account.</p>
<p>This is the same decision that applies to posting in other people's communities, for
the same reason: the last click is the point where a human notices the damage before it
happens. With ads that click costs real money; with communities it costs the domain.</p>
""",
    },
    {
        "id": "seeds",
        "title": "Seed lists",
        "html": """
<p>The scan needs starting points. Three routes, in this order: what you enter yourself
(you know your niche), what the API suggests, and the search paths that can be built from
the keywords alone.</p>
<p>In all three cases the same applies: <b>these are candidates, not facts.</b> Every
entry is checked against the real source during the scan - whatever no longer exists
drops out. That is exactly why suggestions from a language model are usable here: the
scanner pushes back.</p>
""",
    },
    {
        "id": "scan",
        "title": "The scan",
        "html": """
<p>The scan checks the forums on your seed list for reachability, looks for their rules
pages, and harvests links to further forums from their front pages, which it then checks
as well. Unreachable sites slide to the bottom of the list automatically.</p>
<p>With Reddit approval in place the subreddit search joins in: keyword search across the
official API, then one hop over sidebar mentions, then a deep scan of the most promising
candidates for rules and activity.</p>
<p>The scan is polite by design - a fixed pause between requests, an honest user agent,
backoff on rate limits. It takes longer that way. That is intentional.</p>
""",
    },
    {
        "id": "manual_add",
        "title": "Adding communities by hand",
        "html": """
<p>Anything the scan cannot reach you can enter yourself. For a subreddit the name is
enough; for a forum the URL.</p>
<p>The important field is the one for the <b>rules</b>. Paste the community's rules in
there and they go through exactly the same analysis as automatically fetched ones - same
traffic light, same quotes. That is the way to work with Reddit without API approval:
open the sidebar, copy the rules, paste them in.</p>
""",
    },
    {
        "id": "traffic_light",
        "title": "Reading the traffic light",
        "html": """
<table>
  <tr><td>green</td><td>no promotion ban found in the rules - post, but post something
    worth reading</td></tr>
  <tr><td>amber</td><td>allowed with conditions: ratio, flair, collection thread,
    moderator approval - work the checklist</td></tr>
  <tr><td>red</td><td>self-promotion explicitly forbidden - do not post</td></tr>
  <tr><td>grey</td><td>rules could not be fetched - read them yourself</td></tr>
</table>
<p>For every assessment the app shows the <b>original wording</b> it rests on. The
analysis is a heuristic, not a substitute for reading - and it is the most thoroughly
tested part of the code, because a false green here costs the domain.</p>
<p>One deliberate decision: "No spam" appears in almost every rule list and rarely means
a promotion ban. It produces an amber condition, not a red verdict. If it turned things
red, half the list would fall away for nothing.</p>
""",
    },
    {
        "id": "drafts",
        "title": "Drafts and angles",
        "html": """
<table>
  <tr><td>Share a resource</td><td>green communities, direct usefulness</td></tr>
  <tr><td>Ask for corrections</td><td>specialist communities - works best there</td></tr>
  <tr><td>Show the project</td><td>developer and project communities</td></tr>
  <tr><td>A question with context</td><td>communities with a ratio rule</td></tr>
  <tr><td>Forum introduction</td><td>classic forums</td></tr>
</table>
<p>All templates follow one rule: <b>value first, link second</b>.</p>
<p>Templates cannot translate. If the target community is English-speaking and the
product copy in the profile is only German, the draft stays German - and the app says so
explicitly rather than shipping a half-German post. The AI draft does translate, because
it writes from scratch.</p>
""",
    },
    {
        "id": "campaign",
        "title": "Campaign and posting mode",
        "html": """
<p><i>Prepare campaign</i> writes a draft for every suitable community, skips the red
ones, attaches the conditions as a checklist, and spreads the dates so the daily limit
holds.</p>
<p><i>Posting mode</i> then walks you through the queue one station at a time: text on
the clipboard, form open, you read it over and send. After each one the app records it in
the history, which is what the safety catch counts against.</p>
""",
    },
    {
        "id": "auto",
        "title": "Fully automatic channels",
        "html": """
<p>Two channels publish without asking: a Discord webhook and a Mastodon account. Both
work only where you have the rights yourself - a webhook has to be created by someone
with server permissions, and the Mastodon token is yours.</p>
<p>That is the whole difference. In your own channels automation is fine. In other
people's it is spam, regardless of how good the text is.</p>
""",
    },
    {
        "id": "reddit",
        "title": "The Reddit API and its approval",
        "html": """
<p>Reddit's Responsible Builder Policy has allowed no self-service access since late
2025: approval is required before any programmatic access to Reddit data.</p>
<p>Without approval the automatic subreddit search stays empty. Everything else works
without restriction, and subreddits can be added by hand. There is no workaround and
there should not be one - scraping without approval risks exactly what this tool exists
to prevent.</p>
<p>With approval: create an app of type <i>script</i> at reddit.com/prefs/apps, put the
client ID and secret into Settings, and use <i>Test connection</i>. The app reads only
and has no write access whatsoever.</p>
""",
    },
    {
        "id": "guard",
        "title": "The safety catch",
        "html": """
<p>Two brakes, both adjustable in Settings:</p>
<ul>
  <li><b>Daily limit</b> for Reddit posts. Several subreddits on the same day is exactly
    the pattern that reads as spam.</li>
  <li><b>Minimum gap</b> per community, so the same place does not get the same link
    twice within weeks.</li>
</ul>
<p>On top of that, red communities are blocked outright. You can override the catch, but
you have to do it deliberately - and the app tells you what you are overriding.</p>
""",
    },
    {
        "id": "files",
        "title": "Files and technical notes",
        "html": """
<p>The server listens on <code>127.0.0.1</code> only and is not reachable from the
network. There is no cloud service, no account and no telemetry.</p>
<p>Everything lives next to the app as readable JSON. Per product in
<code>data/products/&lt;name&gt;/</code>: communities, queue, history, analysis, strategy,
assets and seed lists. Credentials live in <code>config.json</code>, which is excluded
from version control.</p>
<p>Python 3.10 or newer is enough; no third-party libraries are used, so the app still
starts in a few years' time.</p>
""",
    },
    {
        "id": "limits",
        "title": "Limits, stated honestly",
        "html": """
<ul>
  <li>The rule analysis is a <b>heuristic</b>. It reads patterns, not meaning. Read the
    quotes it shows you.</li>
  <li>Without an API key the copy is <b>plain</b>. It assembles what is in the profile
    and invents nothing, which is right but dry.</li>
  <li>The app has <b>no feedback loop</b>. The UTM tagging is there, but nothing reports
    back which channel actually carried, so channels are still scored by keyword density
    rather than by results.</li>
  <li>Channels beyond Reddit and forums - Lemmy, Hacker News, Discourse instances,
    AlternativeTo - are <b>not connected yet</b>.</li>
  <li>Nothing here replaces knowing your own field. The app can tell you where the rules
    forbid promotion. It cannot tell you whether your product is any good.</li>
</ul>
""",
    },
]


# ===========================================================================
# GERMAN
# ===========================================================================

DE: list[dict[str, Any]] = [
    {
        "id": "idea",
        "title": "Was diese App macht",
        "html": """
<p>Du beschreibst dein Produkt. Die App liest die Produktseite, leitet daraus ab, was das
Produkt ist und für wen, wählt die Kanäle aus, die dafür taugen, und führt sie so weit
aus, wie sich das verantworten lässt. Fünf Stufen, in dieser Reihenfolge:</p>
<table>
  <tr><td>Produktprofil</td><td>Deine Angaben. Alles Weitere hängt daran.</td></tr>
  <tr><td>Analyse</td><td>Was es ist, für wen, und mit welchen Worten gesucht wird.</td></tr>
  <tr><td>Strategie</td><td>Welche Kanäle lohnen - und welche nicht.</td></tr>
  <tr><td>Werbemittel</td><td>Die fertigen Texte dazu, in den Grenzen der Kanäle.</td></tr>
  <tr><td>Kampagne</td><td>Communities, Entwürfe, Termine, Posting-Modus.</td></tr>
</table>
<p>Der Grundsatz hinter allen Texten lautet <b>erst Nutzen, dann Link</b>. Ein Beitrag,
der auch ohne den Link lesenswert wäre, wird nicht als Werbung gelesen - und genau das
ist in Fachcommunities der Unterschied zwischen Zuspruch und Löschung.</p>
<p>Mehrere Produkte laufen nebeneinander. Der Umschalter oben rechts wechselt zwischen
ihnen; Communities, Warteschlange und Verlauf sind je Produkt streng getrennt.</p>
""",
    },
    {
        "id": "quickstart",
        "title": "Schnellstart",
        "html": """
<ol>
  <li><b>Produkt</b>: Name, URL, Einzeiler, Kategorie, Preismodell und Zielgruppe
    eintragen, dann <i>Profil speichern</i>.</li>
  <li><b>Analyse</b> &rarr; <i>Analyse starten</i>. Sie liest die Produktseite und
    gewinnt die Stichwörter, mit denen später alles sucht.</li>
  <li><b>Strategie</b>: den Kanalplan lesen. Er sagt auch, was nicht lohnt und warum.</li>
  <li><b>Werbemittel</b>: die Texte für die Kanäle erzeugen, die du bespielen willst.</li>
  <li><b>Startlisten</b>: Subreddits und Foren eintragen oder vorschlagen lassen.</li>
  <li><b>Scan starten</b> oben rechts.</li>
  <li><b>Kampagne</b> &rarr; <i>Kampagne vorbereiten</i>, dann
    <i>Posting-Modus starten</i>.</li>
</ol>
""",
    },
    {
        "id": "product",
        "title": "Das Produktprofil",
        "html": """
<p>Das Profil ist keine Formalie, sondern der Rohstoff. Der <b>Einzeiler</b> und die
<b>Beschreibung</b> landen wörtlich in deinen Beiträgen - sie sind der Text, den fremde
Menschen lesen werden. <b>Kategorie</b> und <b>Preismodell</b> entscheiden, welche Kanäle
überhaupt angeboten werden. Die <b>Zielgruppe</b> gehört so eng gefasst wie möglich;
„alle&ldquo; ist keine Zielgruppe.</p>
<p>Die <b>Stichwörter</b> sind die Worte deiner Zielgruppe, nicht deine. Der Produktname
gehört nicht dazu - wer ihn kennt, ist schon da.</p>
<p>Das <b>Monatsbudget</b> steuert die bezahlten Kanäle. Steht dort 0, erscheinen sie gar
nicht. Das ist kein Mangel: die meisten Produkte kommen organisch weiter als mit einem
Budget, das zu klein ist, um daraus zu lernen.</p>
""",
    },
    {
        "id": "analysis",
        "title": "Die Analyse",
        "html": """
<p>Ohne API-Schlüssel wird die Produktseite geladen und ausgewertet: Titel, Meta-Angaben,
Überschriften, Wortfrequenzen und Wortpaare. Aus Merkmalen im Text - <code>.exe</code>,
<i>Warenkorb</i>, <i>pro Monat</i>, <i>App Store</i> - rät die App Kategorie und
Preismodell und zeigt zu jeder Einschätzung die <b>Textstelle</b>, aus der sie stammt.
Weicht das von deiner Selbsteinschätzung ab, ist meistens die Seite unklar, nicht die
Analyse falsch.</p>
<p>Mit Anthropic-Schlüssel kommt eine freie Auswertung dazu: Zielgruppensegmente,
Nutzenversprechen, Positionierung, zu erwartende Einwände und die Suchbegriffe, die deine
Zielgruppe tatsächlich benutzt. Die Einwände sind der nützlichste Teil - sie werden später
zur Fachfrage, mit der man in Communities eröffnet, ohne zu werben.</p>
""",
    },
    {
        "id": "strategy",
        "title": "Die Strategie",
        "html": """
<p>Aus Profil und Analyse entsteht ein bewerteter Kanalplan. Jeder Kanal bringt mit,
wofür er taugt, wie viel Aufwand er macht, wann er wirkt und <b>wie weit diese App ihn
übernimmt</b>:</p>
<table>
  <tr><td>Die App veröffentlicht selbst</td><td>Eigene Kanäle - Discord, Mastodon.</td></tr>
  <tr><td>Die App bereitet vor</td><td>Alles fertig, abschicken tut ein Mensch.</td></tr>
  <tr><td>Texte und Anleitung</td><td>Ausgeführt wird von Hand, im eigenen Konto.</td></tr>
</table>
<p>Kanäle, die nicht passen, verschwinden nicht still - sie stehen unter
<b>Verworfen</b> mit Begründung. Ein Vorschlag ohne Gegenprobe ist kein Rat, sondern eine
Meinung. Google Shopping ohne physische Ware ist kein Vorschlag, sondern ein Fehler.</p>
<p>Beim Budget gilt eine Regel, die aus Erfahrung stammt und nicht aus Mathematik:
kleines Budget geht in <b>einen</b> Kanal. 120 Euro auf zwei verteilt heißt zweimal zu
wenig - keiner der beiden sammelt genug Daten, um zu zeigen, ob er taugt. Ein Fünftel
bleibt immer liegen, als Reserve für den Kanal, der sich nach vier Wochen als der beste
herausstellt.</p>
""",
    },
    {
        "id": "assets",
        "title": "Werbemittel",
        "html": """
<p>Die Strategie sagt, <i>was</i> zu tun ist. Der Tab <b>Werbemittel</b> liefert das
Material: Anzeigentexte, Verzeichniseinträge, Store-Einträge, Presse-Kit, Seitentitel und
Meta-Beschreibung, dazu die Ankündigung für die eigenen Kanäle.</p>
<p><b>Die Zeichengrenzen sind hart.</b> Google lehnt eine Anzeigenüberschrift mit 31
Zeichen ab, nicht „ungefähr&ldquo;. Jedes Feld zeigt seine Länge; was gekürzt werden
musste, ist gekennzeichnet, damit du es gegenlesen kannst. KI-Texte laufen durch dieselbe
Prüfung - Sprachmodelle zählen Zeichen notorisch schlecht.</p>
<p><b>Nichts wird erfunden.</b> Die Vorlagen setzen ausschließlich zusammen, was im Profil
und in der Analyse steht. Das macht sie brav, aber wahr. Eine Anzeige, die eine
Eigenschaft behauptet, die es nicht gibt, ist keine Werbung, sondern eine Falschangabe in
deinem Namen - und sie fällt niemandem auf, weil solche Sätze so vertraut klingen.
„Kostenlos testen&ldquo; bei einem Abo verspricht eine Probezeit, die vielleicht gar nicht
existiert.</p>
<p>Je mehr im Profil steht und je gründlicher die Analyse gelaufen ist, desto mehr
Varianten kommen heraus. Stehen dort nur Name und URL, sagt die App das offen, statt die
Lücke mit Floskeln zu füllen.</p>
<p>Bei den Suchanzeigen steht zusätzlich eine Liste <b>auszuschließender
Suchbegriffe</b>. Ohne die verbrennt jede Suchkampagne Geld an Anfragen, die nichts mit
dem Produkt zu tun haben - Leute, die etwas geknackt, gebraucht oder als Jobangebot
suchen. Die Liste ist ein Anfang, kein Ersatz für den Suchbegriffsbericht nach zwei
Wochen.</p>
<p>Jedes Werbemittel bringt seine <b>Zieladresse mit Kampagnenkennzeichnung</b> mit
(UTM). Ohne die weiß hinterher niemand, welcher Kanal getragen hat - und dann bleibt die
Kanalwahl für immer Geschmackssache.</p>
""",
    },
    {
        "id": "money",
        "title": "Warum die App kein Geld ausgibt",
        "html": """
<p>Bezahlte Kampagnen werden vollständig vorbereitet - Anzeigentexte in den
Zeichengrenzen des Kanals, Zielgruppen, Suchbegriffe, Budgetaufteilung - und dann
übergeben. Den Knopf <i>Kampagne aktivieren</i> drückst du in deinem eigenen
Werbekonto.</p>
<p>Das ist dieselbe Entscheidung, die beim Posten in fremde Communities gilt, aus
demselben Grund: Der letzte Klick ist die Stelle, an der ein Mensch den Schaden bemerkt,
bevor er entsteht. Bei Anzeigen kostet dieser Klick echtes Geld, bei Communities die
Domain.</p>
""",
    },
    {
        "id": "seeds",
        "title": "Startlisten",
        "html": """
<p>Der Scan braucht Startpunkte. Drei Wege, in dieser Reihenfolge: was du selbst einträgst
(du kennst deine Nische), was die API vorschlägt, und die Suchpfade, die sich allein aus
den Stichwörtern bauen lassen.</p>
<p>In allen drei Fällen gilt: <b>Das sind Kandidaten, keine Fakten.</b> Jeder Eintrag
wird beim Scan gegen die echte Quelle geprüft - was es nicht mehr gibt, fliegt raus. Genau
deshalb sind auch Vorschläge eines Sprachmodells hier brauchbar: der Scanner hält
dagegen.</p>
""",
    },
    {
        "id": "scan",
        "title": "Der Scan",
        "html": """
<p>Der Scan prüft die Foren deiner Startliste auf Erreichbarkeit, sucht ihre Regelseiten
und erntet aus den Startseiten Links auf weitere Foren, die er ebenfalls prüft. Nicht
erreichbare Seiten rutschen automatisch ans Ende der Liste.</p>
<p>Liegt eine Reddit-Freigabe vor, kommt die Subreddit-Suche dazu: Stichwortsuche über die
offizielle API, dann ein Hop über Sidebar-Erwähnungen, dann ein Tiefenscan der
aussichtsreichsten Kandidaten auf Regeln und Aktivität.</p>
<p>Der Scan ist absichtlich höflich - feste Pause zwischen Anfragen, ehrliche Kennung,
Backoff bei Rate-Limits. Er dauert dadurch länger. Das ist gewollt.</p>
""",
    },
    {
        "id": "manual_add",
        "title": "Communities von Hand aufnehmen",
        "html": """
<p>Was der Scan nicht erreicht, kannst du selbst eintragen. Bei einem Subreddit genügt
der Name, bei einem Forum die URL.</p>
<p>Das wichtige Feld ist das für die <b>Regeln</b>. Fügst du die Regeln der Community dort
ein, laufen sie durch genau dieselbe Analyse wie automatisch geholte - dieselbe Ampel,
dieselben Zitate. Das ist der Weg, mit Reddit ohne API-Freigabe zu arbeiten: Sidebar
öffnen, Regeln kopieren, einfügen.</p>
""",
    },
    {
        "id": "traffic_light",
        "title": "Die Ampel lesen",
        "html": """
<table>
  <tr><td>grün</td><td>kein Werbeverbot in den Regeln gefunden - posten, aber etwas
    Lesenswertes</td></tr>
  <tr><td>gelb</td><td>erlaubt mit Auflagen: Ratio, Flair, Sammelthread, Mod-Freigabe -
    Checkliste abarbeiten</td></tr>
  <tr><td>rot</td><td>Eigenwerbung ausdrücklich verboten - nicht posten</td></tr>
  <tr><td>grau</td><td>Regeln nicht abrufbar - selbst nachlesen</td></tr>
</table>
<p>Zu jeder Einstufung zeigt die App die <b>Originalzitate</b>, aus denen sie stammt. Die
Analyse ist eine Heuristik, kein Ersatz fürs Lesen - und der am gründlichsten getestete
Teil des Codes, weil ein falsches Grün hier die Domain kostet.</p>
<p>Eine bewusste Entscheidung: „No spam&ldquo; steht in fast jeder Regelliste und meint
selten ein Werbeverbot. Es erzeugt eine gelbe Auflage, kein rotes Verdikt. Würde es rot
färben, fiele die halbe Liste grundlos weg.</p>
""",
    },
    {
        "id": "drafts",
        "title": "Entwürfe und Blickwinkel",
        "html": """
<table>
  <tr><td>Ressource teilen</td><td>grüne Communities, direkter Nutzen</td></tr>
  <tr><td>Um Korrekturen bitten</td><td>Fach-Communities - wirkt dort am besten</td></tr>
  <tr><td>Projekt vorstellen</td><td>Entwickler- und Projekt-Communities</td></tr>
  <tr><td>Fachfrage mit Kontext</td><td>Communities mit Ratio-Regel</td></tr>
  <tr><td>Forum-Vorstellung</td><td>klassische Foren</td></tr>
</table>
<p>Alle Vorlagen folgen einer Regel: <b>erst Nutzen, dann Link</b>.</p>
<p>Vorlagen können nicht übersetzen. Ist die Zielcommunity englischsprachig und stehen die
Produkttexte im Profil nur auf Deutsch, bleibt der Entwurf deutsch - und die App sagt das
ausdrücklich, statt einen halb deutschen Beitrag auszuliefern. Der KI-Entwurf übersetzt,
weil er neu schreibt.</p>
""",
    },
    {
        "id": "campaign",
        "title": "Kampagne und Posting-Modus",
        "html": """
<p><i>Kampagne vorbereiten</i> schreibt für jede geeignete Community einen Entwurf,
überspringt die roten, hängt die Auflagen als Checkliste an und verteilt die Termine so,
dass das Tageslimit hält.</p>
<p>Der <i>Posting-Modus</i> führt dich dann Station für Station durch die Warteschlange:
Text in der Zwischenablage, Formular offen, du liest gegen und schickst ab. Nach jedem
Beitrag vermerkt die App ihn im Verlauf - und genau den zählt der Schutzschalter.</p>
""",
    },
    {
        "id": "auto",
        "title": "Vollautomatische Kanäle",
        "html": """
<p>Zwei Kanäle veröffentlichen ohne Rückfrage: ein Discord-Webhook und ein
Mastodon-Konto. Beide funktionieren nur dort, wo du selbst die Rechte hast - einen Webhook
muss jemand mit Serverrechten anlegen, und der Mastodon-Token ist deiner.</p>
<p>Das ist der ganze Unterschied. In eigenen Kanälen ist Automatisierung in Ordnung. In
fremden ist sie Spam, egal wie gut der Text ist.</p>
""",
    },
    {
        "id": "reddit",
        "title": "Die Reddit-API und die Freigabe",
        "html": """
<p>Reddits Responsible Builder Policy lässt seit Ende 2025 keinen
Selbstbedienungs-Zugang mehr zu: Vor jedem programmatischen Zugriff auf Reddit-Daten ist
eine Freigabe nötig.</p>
<p>Ohne Freigabe bleibt die automatische Subreddit-Suche leer. Alles andere funktioniert
uneingeschränkt, und Subreddits lassen sich von Hand aufnehmen. Einen Umweg gibt es nicht
und soll es nicht geben - wer ohne Freigabe scrapt, riskiert genau das, was dieses
Werkzeug verhindern soll.</p>
<p>Mit Freigabe: App vom Typ <i>script</i> unter reddit.com/prefs/apps anlegen, Client-ID
und Secret in den Einstellungen eintragen, <i>Verbindung testen</i>. Die App liest
ausschließlich und hat keinerlei Schreibzugriff.</p>
""",
    },
    {
        "id": "guard",
        "title": "Der Schutzschalter",
        "html": """
<p>Zwei Bremsen, beide in den Einstellungen justierbar:</p>
<ul>
  <li><b>Tageslimit</b> für Reddit-Beiträge. Mehrere Subreddits am selben Tag ist genau
    das Muster, das als Spam erkannt wird.</li>
  <li><b>Mindestabstand</b> je Community, damit dieselbe Stelle nicht innerhalb von
    Wochen zweimal denselben Link bekommt.</li>
</ul>
<p>Dazu werden rote Communities grundsätzlich gesperrt. Du kannst den Schalter
übergehen, aber du musst es absichtlich tun - und die App sagt dir, was du übergehst.</p>
""",
    },
    {
        "id": "files",
        "title": "Dateien und Technik",
        "html": """
<p>Der Server hört ausschließlich auf <code>127.0.0.1</code> und ist aus dem Netzwerk
nicht erreichbar. Es gibt keinen Cloud-Dienst, kein Konto und keine Telemetrie.</p>
<p>Alles liegt als lesbares JSON neben der App. Je Produkt in
<code>data/products/&lt;name&gt;/</code>: Communities, Warteschlange, Verlauf, Analyse,
Strategie, Werbemittel und Startlisten. Zugangsdaten stehen in <code>config.json</code>,
die von der Versionsverwaltung ausgeschlossen ist.</p>
<p>Python 3.10 oder neuer genügt; Fremdbibliotheken werden nicht benutzt, damit die App
auch in einigen Jahren noch startet.</p>
""",
    },
    {
        "id": "limits",
        "title": "Grenzen, ehrlich benannt",
        "html": """
<ul>
  <li>Die Regel-Analyse ist eine <b>Heuristik</b>. Sie liest Muster, nicht Bedeutung.
    Lies die Zitate, die sie dir zeigt.</li>
  <li>Ohne API-Schlüssel sind die Texte <b>brav</b>. Sie setzen zusammen, was im Profil
    steht, und erfinden nichts - das ist richtig, aber trocken.</li>
  <li>Die App hat <b>keine Rückkopplung</b>. Die UTM-Kennzeichnung steht, aber niemand
    meldet zurück, welcher Kanal tatsächlich getragen hat. Kanäle werden deshalb weiter
    nach Stichwortdichte bewertet statt nach Ergebnissen.</li>
  <li>Kanäle jenseits von Reddit und Foren - Lemmy, Hacker News, Discourse-Instanzen,
    AlternativeTo - sind <b>noch nicht angebunden</b>.</li>
  <li>Nichts hier ersetzt Kenntnis des eigenen Fachs. Die App kann dir sagen, wo die
    Regeln Werbung verbieten. Ob dein Produkt etwas taugt, kann sie dir nicht sagen.</li>
</ul>
""",
    },
]


MANUAL: dict[str, list[dict[str, Any]]] = {"en": EN, "de": DE}

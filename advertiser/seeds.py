"""
Startlisten fuer die Suche.

WICHTIG: Das sind Kandidaten, keine gesicherten Fakten. Jeder Eintrag wird beim
Scan gegen die echte Quelle geprueft - was es nicht (mehr) gibt, fliegt automatisch
raus und wird im Bericht als "nicht erreichbar" gefuehrt. Die Liste ist bewusst
breit angelegt; die Bewertung uebernimmt der Scanner, nicht diese Datei.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Reddit: Saat-Subreddits. Der Scanner erweitert diese Liste automatisch ueber
# die Stichwortsuche und ueber r/<sub>-Erwaehnungen in den Sidebars (1 Hop).
# ---------------------------------------------------------------------------

SUBREDDIT_SEEDS: list[str] = [
    # Kernthema Daemonologie / Demonolatry
    "Demonolatry", "DemonolatryPractices", "demonology", "Goetia", "GoeticMagick",
    "demons", "Daemonolatry", "InfernalDivinity",
    # Okkultismus allgemein
    "occult", "Occultism", "OccultConspiracy", "EsotericOccult", "esotericism",
    "Magick", "ChaosMagick", "ceremonialmagic", "SolomonicMagic", "Thelema",
    "Grimoires", "Sigils", "SigilMagick", "spiritwork", "Spirituality",
    # Linke Hand / Satanismus / Luziferianismus
    "Satanism", "TheisticSatanism", "SatanicTemple_Reddit", "Luciferianism",
    "LeftHandPath", "Setianism", "DemonicPossession",
    # Hexerei / Praxis (oft strengere Promo-Regeln - Scanner prueft das)
    "witchcraft", "Witch", "SASSWitches", "pagan", "Wicca", "folklore",
    "mythology", "Divination", "Tarot",
    # Wissens-/Buch-nahe Communities (gute Zielgruppe fuer eine Enzyklopaedie)
    "AskOccult", "occultbooks", "Esoteric", "religion", "AcademicBiblical",
    # Communities, in denen Projekte ausdruecklich geteilt werden duerfen
    "SideProject", "InternetIsBeautiful", "coolgithubprojects", "webdev",
    "SomebodyMakeThis", "DigitalHumanities", "Worldbuilding",
]

# Subreddits, die erfahrungsgemaess reine Werbung sind. Nur als Notnagel und
# bewusst niedrig priorisiert - Traffic von dort ist praktisch wertlos.
LOW_VALUE_SUBS: set[str] = {
    "promote", "advertise", "AdvertiseYourVideos", "SelfPromotionForYou",
    "PromoteYourProject", "shamelessplug", "PromoteYourWebsite",
}

# ---------------------------------------------------------------------------
# Foren & Wikis: Startliste. Der Scanner prueft Erreichbarkeit, sucht nach einem
# Registrierungs-/Regel-Hinweis und erntet ausgehende Links auf weitere Foren.
# ---------------------------------------------------------------------------

FORUM_SEEDS: list[dict] = [
    {"name": "Studio Arcanis", "url": "https://www.studioarcanis.com/",
     "note": "Langlebiges Forum fuer zeremonielle Magie und Goetie."},
    {"name": "The Cauldron", "url": "https://www.ecauldron.com/",
     "note": "Aeltestes Pagan-/Okkult-Forum, moderiert, hohe Textqualitaet."},
    {"name": "Astral Pulse", "url": "https://www.astralpulse.com/",
     "note": "Astralprojektion & Geisterarbeit, aktive Community."},
    {"name": "Spiritual Forums", "url": "https://www.spiritualforums.com/",
     "note": "Grosses Allgemein-Forum mit Okkult-Unterboards."},
    {"name": "Occult Forum", "url": "https://occultforum.org/",
     "note": "Klassisches Okkult-Board."},
    {"name": "Become A Living God (Forum)", "url": "https://forum.becomealivinggod.com/",
     "note": "Explizit Demonolatry/Left Hand Path."},
    {"name": "Occult World", "url": "https://occult-world.com/",
     "note": "Wiki-artige Enzyklopaedie - Kooperation/Verlinkung statt Werbepost."},
    {"name": "Sacred Texts", "url": "https://sacred-texts.com/",
     "note": "Quellenarchiv - als Referenz, nicht als Postingziel."},
    {"name": "Esoteric Library", "url": "https://www.esotericlibrary.com/",
     "note": "Linkverzeichnis, oft mit Eintragsmoeglichkeit."},
    {"name": "Hermetic Library", "url": "https://hermetic.com/",
     "note": "Kuratierte Sammlung, nimmt gelegentlich Ressourcen auf."},
]

# Domains, auf denen eigene Links grundsaetzlich tabu sind (Interessenkonflikt).
FORUM_BLOCKLIST: set[str] = {
    "wikipedia.org", "wikimedia.org", "wikidata.org",
}

# Hersteller von Forensoftware und Plattform-Startseiten - beim Link-Ernten
# tauchen die staendig auf, sind aber keine Communities.
FORUM_VENDOR_BLOCKLIST: tuple[str, ...] = (
    "phpbb.com", "phpbb.de", "discourse.org", "xenforo.com", "invisioncommunity.com",
    "simplemachines.org", "mybb.com", "proboards.com", "vbulletin.com", "tapatalk.com",
    "wordpress.org", "wordpress.com", "cloudflare.com", "godaddy.com", "wix.com",
    "squarespace.com", "google.com", "youtube.com", "facebook.com", "twitter.com",
    "x.com", "instagram.com", "discord.com", "discord.gg", "patreon.com", "amazon.com",
    "paypal.com", "github.com", "mozilla.org", "adobe.com",
)

# Heuristik, um beim Link-Ernten echte Foren zu erkennen.
FORUM_URL_HINTS: tuple[str, ...] = (
    "/forum", "/forums", "/board", "/boards", "/community", "/viewforum",
    "phpbb", "smf", "xenforo", "invision", "discourse", "vbulletin", "proboards",
)

# ---------------------------------------------------------------------------
# Discord: Einladungslinks laufen ab, deshalb werden hier bewusst KEINE
# hartkodiert. Stattdessen Suchpfade, die die App oeffnet - gefundene Server
# traegst du einmalig in der GUI ein, danach kennt die App sie dauerhaft.
# ---------------------------------------------------------------------------

DISCORD_SEARCH_URLS: list[dict] = [
    {"name": "Disboard: occult", "url": "https://disboard.org/servers/tag/occult"},
    {"name": "Disboard: demonolatry", "url": "https://disboard.org/search?keyword=demonolatry"},
    {"name": "Disboard: witchcraft", "url": "https://disboard.org/servers/tag/witchcraft"},
    {"name": "Disboard: satanism", "url": "https://disboard.org/search?keyword=satanism"},
    {"name": "Top.gg Server: occult", "url": "https://top.gg/servers/search?q=occult"},
    {"name": "Discadia: occult", "url": "https://discadia.com/servers/?q=occult"},
    {"name": "Discord Me: occult", "url": "https://discord.me/servers/tag/occult"},
]

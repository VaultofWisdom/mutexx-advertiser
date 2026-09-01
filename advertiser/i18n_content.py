"""
Translation catalogue, long form: the channel catalogue and the asset specifications.

Kept apart from i18n.py purely so both files stay readable. These are the sentences a
user actually reads while deciding where to spend a month of work or a month of budget,
so they are written as advice, not as labels.
"""

from __future__ import annotations

# ===========================================================================
# ENGLISH
# ===========================================================================

EN_CONTENT: dict[str, str] = {
    # -- Channels: owned -----------------------------------------------------
    "channel.own_channels.name": "Owned channels",
    "channel.own_channels.what": "Your own Discord server, Mastodon, X, your own mailing list. "
                                 "The reach is small, but nobody can argue about permission and "
                                 "the people there are already warm.",
    "channel.own_channels.first_step": "Add a Discord webhook or a Mastodon token under Auto "
                                       "channels and send the test post.",
    "channel.own_channels.risk": "None - these are your own channels.",

    "channel.product_page.name": "Sharpen the product page",
    "channel.product_page.what": "Title, meta description, the first screenful and the preview "
                                 "image. Every other channel leads here; if the page is unclear, "
                                 "everything upstream of it evaporates.",
    "channel.product_page.first_step": "Open the analysis and check whether the title and meta "
                                       "description carry the value proposition it found.",
    "channel.product_page.risk": "None.",

    # -- Channels: organic ---------------------------------------------------
    "channel.communities.name": "Communities and forums",
    "channel.communities.what": "The specialist communities your audience already sits in. Slow, "
                                "but the people who arrive this way stay. This is the part this "
                                "app does best.",
    "channel.communities.first_step": "Run the scan, then prepare the campaign. Red communities "
                                      "are skipped, amber ones come with a checklist.",
    "channel.communities.risk": "Spreading the same link everywhere costs you the domain, not just "
                                "the account. The app's safety catch exists to slow exactly that "
                                "down.",

    "channel.directories.name": "Directories and portals",
    "channel.directories.what": "AlternativeTo, Product Hunt, Softpedia, download portals, "
                                "itch.io, F-Droid. Listings are wanted rather than tolerated, and "
                                "they keep ranking.",
    "channel.directories.first_step": "Generate the portal descriptions in short, medium and long, "
                                      "then create the listings one after another.",
    "channel.directories.risk": "Some portals want money for a highlighted spot. The free listing "
                                "is enough.",

    "channel.seo_content.name": "Content and search engines",
    "channel.seo_content.what": "Writing about the questions your audience types in before they "
                                "decide. Takes months, then carries on with no running cost.",
    "channel.seo_content.first_step": "Sort the search terms from the analysis by intent and write "
                                      "one piece for each of the three most common.",
    "channel.seo_content.risk": "The slowest channel there is. If you need results in four weeks, "
                                "do not start here.",

    "channel.app_store.name": "Optimise the store listing",
    "channel.app_store.what": "App Store, Google Play, Steam, Microsoft Store. The listing itself "
                              "is the channel - title, subtitle, images, keywords.",
    "channel.app_store.first_step": "Generate store copy within each store's character limits and "
                                    "line the screenshots up behind it.",
    "channel.app_store.risk": "Some stores put changes through review again.",

    "channel.open_source.name": "Visibility in the open",
    "channel.open_source.what": "A README that says something, topic tags, a place on the right "
                                "awesome lists, answers in other people's issues. Only works with "
                                "open source.",
    "channel.open_source.first_step": "Put the repository link in the profile, then derive the "
                                      "topic tags and the right awesome lists from the analysis.",
    "channel.open_source.risk": "Without a public repository this channel simply does not exist.",

    "channel.press.name": "Trade press and blogs",
    "channel.press.what": "Editors and individual writers who cover exactly this subject. One hit "
                          "is worth more than fifty forum posts - and takes longer.",
    "channel.press.first_step": "Generate the press kit, then write to people individually. Never "
                                "as a mailing list.",
    "channel.press.risk": "Mass mail to editors goes unread into the bin and burns the contact for "
                          "good.",

    "channel.newsletter.name": "Your own mailing list",
    "channel.newsletter.what": "The only reach that genuinely belongs to you. Worth starting the "
                               "day anyone at all lands on the page.",
    "channel.newsletter.first_step": "Put a signup field on the product page, then use the "
                                     "changelog as the occasion for the first issue.",
    "channel.newsletter.risk": "A list with nothing to say falls asleep after three issues.",

    "channel.video.name": "Video and demonstration",
    "channel.video.what": "Two minutes of screen capture showing what the product does. Reusable "
                          "in almost every other channel.",
    "channel.video.first_step": "Record the one task the product does best - no preamble, no music.",
    "channel.video.risk": "A video that takes 40 seconds to get to the point does not get watched.",

    # -- Channels: paid ------------------------------------------------------
    "channel.google_search_ads.name": "Google search ads",
    "channel.google_search_ads.what": "Ads on search terms with visible buying intent. Works "
                                      "immediately and stops working immediately when the budget "
                                      "runs out.",
    "channel.google_search_ads.first_step": "Generate ad groups and copy within Google's character "
                                            "limits, load them into your own account, start with a "
                                            "small daily budget.",
    "channel.google_search_ads.risk": "Without negative keywords the budget burns on queries that "
                                      "have nothing to do with the product.",

    "channel.google_shopping.name": "Google Shopping",
    "channel.google_shopping.what": "Product ads with a picture and a price, right in the search "
                                    "results. Requires a product feed and actual goods.",
    "channel.google_shopping.first_step": "Set up a Merchant Center account and build the product "
                                          "feed - without a clean feed nothing here works at all.",
    "channel.google_shopping.risk": "The feed is the real work. Bad data gets the whole account "
                                    "rejected.",

    "channel.meta_ads.name": "Meta ads (Facebook, Instagram)",
    "channel.meta_ads.what": "Ads for people who are not searching but scrolling. Needs an image "
                             "or a video that works with the sound off.",
    "channel.meta_ads.first_step": "Prepare three ad variants and two audiences, set them up in "
                                   "Ads Manager, run them against each other.",
    "channel.meta_ads.risk": "Specialist audiences barely react here. For developer tools the "
                             "money is usually lost.",

    "channel.reddit_ads.name": "Reddit ads",
    "channel.reddit_ads.what": "Ads inside individual subreddits. The honest way into communities "
                               "where self-promotion is forbidden as a post - and noticeably "
                               "cheaper than Meta.",
    "channel.reddit_ads.first_step": "Take the red communities from the scan as your ad targets - "
                                     "you reach the same people without breaking the rules.",
    "channel.reddit_ads.risk": "Reddit users spot marketing language instantly. The ad has to read "
                               "like a post, not like a brochure.",

    "channel.microsoft_ads.name": "Microsoft ads (Bing)",
    "channel.microsoft_ads.what": "Noticeably cheaper clicks than Google, smaller reach. The "
                                  "audience sits at Windows machines in offices more often than "
                                  "average.",
    "channel.microsoft_ads.first_step": "Import the Google campaign rather than rebuilding it - "
                                        "Microsoft offers the import explicitly.",
    "channel.microsoft_ads.risk": "Little search volume. Too thin as your only paid channel.",

    "channel.video_ads.name": "YouTube and TikTok ads",
    "channel.video_ads.what": "Moving pictures at a broad audience. Expensive to produce, worth it "
                              "only once the cheaper channels are exhausted.",
    "channel.video_ads.first_step": "First make an organic video that demonstrably works, then "
                                    "promote exactly that one.",
    "channel.video_ads.risk": "Without an existing video this is not a channel, it is a production "
                              "job.",

    "channel.sponsoring.name": "Newsletter and podcast sponsorship",
    "channel.sponsoring.what": "A slot in something your audience reads voluntarily. Fixed prices, "
                               "no bidding, and the mention lands as a personal recommendation.",
    "channel.sponsoring.first_step": "Find the three newsletters your audience actually reads and "
                                     "ask for their media kit.",
    "channel.sponsoring.risk": "One-off placements evaporate. It is the third mention that works.",

    # -- Assets --------------------------------------------------------------
    "asset.seo_meta.name": "Title and meta description",
    "asset.seo_meta.what": "What shows up in Google's results list. The cheapest lever there is - "
                           "every other channel leads here.",
    "asset.seo_meta.field.title": "Page title",
    "asset.seo_meta.hint.title": "Google truncates anything longer. Value before brand name.",
    "asset.seo_meta.field.description": "Meta description",
    "asset.seo_meta.hint.description": "Not a ranking factor, but it decides the click.",
    "asset.seo_meta.field.og_title": "Title when shared",
    "asset.seo_meta.hint.og_title": "What appears as a preview in Discord, Slack and social feeds.",
    "asset.seo_meta.field.og_description": "Description when shared",
    "asset.seo_meta.hint.og_description": "Shorter than the meta description - preview cards are tight.",

    "asset.directory_listing.name": "Directory and portal listing",
    "asset.directory_listing.what": "For AlternativeTo, Product Hunt, Softpedia, download portals, "
                                    "itch.io. Every portal wants a different length, so here are "
                                    "all three.",
    "asset.directory_listing.field.tagline": "One-liner",
    "asset.directory_listing.hint.tagline": "The line directly under the name.",
    "asset.directory_listing.field.short": "Short description",
    "asset.directory_listing.hint.short": "The usual length in directories.",
    "asset.directory_listing.field.long": "Full description",
    "asset.directory_listing.hint.long": "For portals with a product page of their own.",

    "asset.own_channel_post.name": "Announcement for your own channels",
    "asset.own_channel_post.what": "Discord and Mastodon. These are the only texts that go out "
                                   "fully automatically - they are your channels.",
    "asset.own_channel_post.field.discord": "Discord",
    "asset.own_channel_post.hint.discord": "Formatting with ** and * is allowed.",
    "asset.own_channel_post.field.mastodon": "Mastodon",
    "asset.own_channel_post.hint.mastodon": "Most instances allow 500 characters.",

    "asset.google_search_ads.name": "Google search ads",
    "asset.google_search_ads.what": "A responsive search ad: Google mixes headlines and "
                                    "descriptions itself. The more variants, the more the "
                                    "algorithm has to combine.",
    "asset.google_search_ads.note": "Without negative keywords every search campaign burns money "
                                    "on queries unrelated to the product. The list below is a "
                                    "start, not a substitute for the search-terms report after "
                                    "two weeks.",
    "asset.google_search_ads.field.headlines": "Headlines",
    "asset.google_search_ads.hint.headlines": "Google wants at least 3 and recommends 15. Each has "
                                              "to stand on its own.",
    "asset.google_search_ads.field.descriptions": "Descriptions",
    "asset.google_search_ads.hint.descriptions": "At least 2, at most 4.",
    "asset.google_search_ads.field.paths": "Display path",
    "asset.google_search_ads.hint.paths": "Cosmetic text after the domain; it does not have to exist.",

    "asset.microsoft_ads.name": "Microsoft ads (Bing)",
    "asset.microsoft_ads.what": "The same character limits as Google. Microsoft offers an import "
                                "of the Google campaign explicitly - that is the faster route.",
    "asset.microsoft_ads.field.headlines": "Headlines",
    "asset.microsoft_ads.hint.headlines": "As with Google.",
    "asset.microsoft_ads.field.descriptions": "Descriptions",
    "asset.microsoft_ads.hint.descriptions": "As with Google.",

    "asset.meta_ads.name": "Meta ads (Facebook, Instagram)",
    "asset.meta_ads.what": "Here the copy carries less than the image. These lines are what sits "
                           "beside the picture - without a picture none of them is worth anything.",
    "asset.meta_ads.note": "Specialist audiences barely react here. For developer tools the money "
                           "is usually gone before the first ad has learned anything.",
    "asset.meta_ads.field.primary_text": "Primary text",
    "asset.meta_ads.hint.primary_text": "Longer is allowed but gets cut off after 125 characters.",
    "asset.meta_ads.field.headline": "Headline",
    "asset.meta_ads.hint.headline": "Sits in bold under the image.",
    "asset.meta_ads.field.description": "Description",
    "asset.meta_ads.hint.description": "Not shown in every placement.",

    "asset.reddit_ads.name": "Reddit ads",
    "asset.reddit_ads.what": "The honest way into communities where self-promotion is forbidden as "
                             "a post. The copy has to read like a post, not like a brochure.",
    "asset.reddit_ads.note": "Reddit users spot marketing language instantly. No superlatives, no "
                             "exclamation marks - otherwise the ad is not ignored, it is mocked.",
    "asset.reddit_ads.field.headline": "Headline",
    "asset.reddit_ads.hint.headline": "300 are technically allowed. Past 100 nobody reads it.",
    "asset.reddit_ads.field.body": "Body text",
    "asset.reddit_ads.hint.body": "Only visible in some ad formats.",

    "asset.store_listing.name": "Store listing",
    "asset.store_listing.what": "App Store, Google Play and Steam. The listing itself is the channel.",
    "asset.store_listing.field.app_name": "Name in the store",
    "asset.store_listing.hint.app_name": "App Store and Play both allow 30.",
    "asset.store_listing.field.subtitle": "Subtitle",
    "asset.store_listing.hint.subtitle": "App Store. It is searched too.",
    "asset.store_listing.field.short_description": "Short description",
    "asset.store_listing.hint.short_description": "Google Play. Sits right at the top.",
    "asset.store_listing.field.steam_short": "Steam short description",
    "asset.store_listing.hint.steam_short": "Steam. Appears in the library and in search.",
    "asset.store_listing.field.full_description": "Full description",
    "asset.store_listing.hint.full_description": "Play and App Store.",
    "asset.store_listing.field.keywords": "Keywords",
    "asset.store_listing.hint.keywords": "App Store, comma separated, no space after the comma.",

    "asset.press_kit.name": "Press kit",
    "asset.press_kit.what": "What an editor needs in order to write without asking you anything. "
                            "Send it individually - mass mail burns the contact for good.",
    "asset.press_kit.field.headline": "Headline",
    "asset.press_kit.hint.headline": "What happened, not how great it is.",
    "asset.press_kit.field.lead": "Lead paragraph",
    "asset.press_kit.hint.lead": "Who, what, when, where, why - in one paragraph.",
    "asset.press_kit.field.body": "Body",
    "asset.press_kit.hint.body": "Most important first. Editors cut from the bottom.",
    "asset.press_kit.field.boilerplate": "About the project",
    "asset.press_kit.hint.boilerplate": "The identical paragraph at the end of every release.",
    "asset.press_kit.field.facts": "Facts at a glance",
    "asset.press_kit.hint.facts": "Price, platforms, version, address.",

    # -- Press kit copy ------------------------------------------------------
    "press.available_now": "{product} is available now",
    "press.aimed_at": "It is aimed at {audience}.",
    "press.in_detail": "In detail:",
    "press.fact.product": "Product",
    "press.fact.version": "Version",
    "press.fact.type": "Type",
    "press.fact.price": "Price",
    "press.fact.regions": "Regions",
    "press.fact.web": "Web",
    "listing.what_it_does": "What it does:",
    "listing.who_for": "Who it is for:",
    "listing.pricing": "Pricing:",
}


# ===========================================================================
# GERMAN
# ===========================================================================

DE_CONTENT: dict[str, str] = {
    # -- Kanäle: eigen -------------------------------------------------------
    "channel.own_channels.name": "Eigene Kanäle",
    "channel.own_channels.what": "Eigener Discord-Server, Mastodon, X, eigener Verteiler. Die "
                                 "Reichweite ist klein, aber über die Erlaubnis lässt sich nicht "
                                 "streiten, und die Leute dort sind vorgewärmt.",
    "channel.own_channels.first_step": "Unter Auto-Kanäle einen Discord-Webhook oder Mastodon-Token "
                                       "hinterlegen und den Testbeitrag abschicken.",
    "channel.own_channels.risk": "Keins - das sind deine eigenen Kanäle.",

    "channel.product_page.name": "Produktseite schärfen",
    "channel.product_page.what": "Titel, Meta-Beschreibung, erste Bildschirmseite und Vorschaubild. "
                                 "Jeder andere Kanal führt hierher; ist die Seite unklar, "
                                 "verpufft alles davor.",
    "channel.product_page.first_step": "Analyse öffnen und prüfen, ob Titel und Meta-Beschreibung "
                                       "das Nutzenversprechen enthalten, das sie gefunden hat.",
    "channel.product_page.risk": "Keins.",

    # -- Kanäle: organisch ---------------------------------------------------
    "channel.communities.name": "Communities und Foren",
    "channel.communities.what": "Die Fachcommunities, in denen deine Zielgruppe ohnehin sitzt. "
                                "Langsam, aber die Leute, die so kommen, bleiben. Das ist der "
                                "Teil, den diese App am besten kann.",
    "channel.communities.first_step": "Scan starten, dann Kampagne vorbereiten. Rote Communities "
                                      "werden übersprungen, gelbe bekommen eine Checkliste.",
    "channel.communities.risk": "Wer denselben Link überall verteilt, verliert die Domain, nicht "
                                "nur das Konto. Der Schutzschalter der App bremst genau das.",

    "channel.directories.name": "Verzeichnisse und Portale",
    "channel.directories.what": "AlternativeTo, Product Hunt, Softpedia, Download-Portale, "
                                "itch.io, F-Droid. Einträge sind erwünscht statt geduldet und "
                                "ranken dauerhaft.",
    "channel.directories.first_step": "Portalbeschreibungen in kurz, mittel und lang erzeugen "
                                      "lassen und die Einträge der Reihe nach anlegen.",
    "channel.directories.risk": "Manche Portale wollen Geld für Hervorhebung. Der freie Eintrag "
                                "genügt.",

    "channel.seo_content.name": "Inhalte und Suchmaschinen",
    "channel.seo_content.what": "Texte zu den Fragen, die deine Zielgruppe vor der Entscheidung "
                                "eintippt. Braucht Monate, trägt dann aber ohne laufende Kosten.",
    "channel.seo_content.first_step": "Die Suchbegriffe aus der Analyse nach Absicht sortieren und "
                                      "zu den drei häufigsten je einen Text schreiben.",
    "channel.seo_content.risk": "Der langsamste Kanal von allen. Wer in vier Wochen Ergebnisse "
                                "braucht, fängt hier nicht an.",

    "channel.app_store.name": "Store-Eintrag optimieren",
    "channel.app_store.what": "App Store, Google Play, Steam, Microsoft Store. Der Eintrag selbst "
                              "ist der Kanal - Titel, Untertitel, Bilder, Suchbegriffe.",
    "channel.app_store.first_step": "Store-Texte in den Zeichengrenzen des jeweiligen Stores "
                                    "erzeugen lassen und die Bildstrecke danach ausrichten.",
    "channel.app_store.risk": "Änderungen brauchen bei manchen Stores eine erneute Prüfung.",

    "channel.open_source.name": "Sichtbarkeit im Quelloffenen",
    "channel.open_source.what": "Eine README, die etwas sagt, Themen-Tags, ein Platz auf den "
                                "passenden Awesome-Listen, Antworten in fremden Issues. Wirkt nur "
                                "bei offenem Quellcode.",
    "channel.open_source.first_step": "Repo-Link im Profil eintragen, dann Themen-Tags und die "
                                      "passenden Awesome-Listen aus der Analyse ableiten.",
    "channel.open_source.risk": "Ohne öffentliches Repository gibt es diesen Kanal schlicht nicht.",

    "channel.press.name": "Fachpresse und Blogs",
    "channel.press.what": "Redaktionen und Einzelautoren, die über genau dieses Thema schreiben. "
                          "Ein Treffer bringt mehr als fünfzig Forenbeiträge - und dauert länger.",
    "channel.press.first_step": "Presse-Kit erzeugen lassen, dann einzeln anschreiben. Niemals im "
                                "Verteiler.",
    "channel.press.risk": "Rundmails an Redaktionen landen ungelesen im Papierkorb und verbrennen "
                          "den Kontakt dauerhaft.",

    "channel.newsletter.name": "Eigener Verteiler",
    "channel.newsletter.what": "Die einzige Reichweite, die dir wirklich gehört. Lohnt ab dem Tag, "
                               "an dem überhaupt jemand auf der Seite landet.",
    "channel.newsletter.first_step": "Anmeldefeld auf die Produktseite, dann den Changelog als "
                                     "Anlass für die erste Ausgabe nehmen.",
    "channel.newsletter.risk": "Ein Verteiler ohne Anlass zum Schreiben schläft nach drei Ausgaben "
                               "ein.",

    "channel.video.name": "Video und Demonstration",
    "channel.video.what": "Zwei Minuten Bildschirmaufnahme, die zeigt, was das Produkt tut. Lässt "
                          "sich in fast jeden anderen Kanal weiterverwenden.",
    "channel.video.first_step": "Den einen Arbeitsschritt aufnehmen, den das Produkt am besten kann "
                                "- ohne Vorrede, ohne Musik.",
    "channel.video.risk": "Ein Video, das erst nach 40 Sekunden zur Sache kommt, wird nicht gesehen.",

    # -- Kanäle: bezahlt -----------------------------------------------------
    "channel.google_search_ads.name": "Google-Suchanzeigen",
    "channel.google_search_ads.what": "Anzeigen auf Suchbegriffe mit erkennbarer Kaufabsicht. "
                                      "Wirkt sofort und hört sofort auf zu wirken, wenn das Budget "
                                      "endet.",
    "channel.google_search_ads.first_step": "Anzeigengruppen und Texte in den Google-Zeichengrenzen "
                                            "erzeugen lassen, im eigenen Konto einspielen, mit "
                                            "kleinem Tagesbudget starten.",
    "channel.google_search_ads.risk": "Ohne auszuschließende Suchbegriffe verbrennt das Budget an "
                                      "Suchanfragen, die nichts mit dem Produkt zu tun haben.",

    "channel.google_shopping.name": "Google Shopping",
    "channel.google_shopping.what": "Produktanzeigen mit Bild und Preis direkt in der Suche. Setzt "
                                    "einen Produktdatenfeed und echte Ware voraus.",
    "channel.google_shopping.first_step": "Merchant-Center-Konto anlegen und den Produktdatenfeed "
                                          "aufbauen - ohne sauberen Feed läuft hier gar nichts.",
    "channel.google_shopping.risk": "Der Feed ist die eigentliche Arbeit. Fehlerhafte Daten führen "
                                    "zur Ablehnung des gesamten Kontos.",

    "channel.meta_ads.name": "Meta-Anzeigen (Facebook, Instagram)",
    "channel.meta_ads.what": "Anzeigen an Menschen, die nicht suchen, sondern blättern. Braucht ein "
                             "Bild oder Video, das ohne Ton funktioniert.",
    "channel.meta_ads.first_step": "Drei Anzeigenvarianten und zwei Zielgruppen vorbereiten lassen, "
                                   "im Werbeanzeigenmanager anlegen, gegeneinander laufen lassen.",
    "channel.meta_ads.risk": "Fachpublikum reagiert hier kaum. Bei Entwicklerwerkzeugen ist das "
                             "Geld meist verloren.",

    "channel.reddit_ads.name": "Reddit-Anzeigen",
    "channel.reddit_ads.what": "Anzeigen in einzelnen Subreddits. Der ehrliche Weg in Communities, "
                               "in denen Eigenwerbung als Beitrag verboten ist - und deutlich "
                               "günstiger als Meta.",
    "channel.reddit_ads.first_step": "Die roten Communities aus dem Scan als Anzeigenziel nehmen - "
                                     "dort erreicht man dieselben Leute, ohne die Regeln zu brechen.",
    "channel.reddit_ads.risk": "Reddit-Nutzer erkennen Werbesprache sofort. Der Anzeigentext muss "
                               "klingen wie ein Beitrag, nicht wie ein Prospekt.",

    "channel.microsoft_ads.name": "Microsoft-Anzeigen (Bing)",
    "channel.microsoft_ads.what": "Deutlich billigere Klicks als bei Google, kleinere Reichweite. "
                                  "Die Zielgruppe sitzt überdurchschnittlich oft an Windows-"
                                  "Rechnern im Büro.",
    "channel.microsoft_ads.first_step": "Die Google-Kampagne importieren, statt sie neu zu bauen - "
                                        "Microsoft bietet den Import ausdrücklich an.",
    "channel.microsoft_ads.risk": "Wenig Suchvolumen. Als einziger bezahlter Kanal zu dünn.",

    "channel.video_ads.name": "YouTube- und TikTok-Anzeigen",
    "channel.video_ads.what": "Bewegtbild an ein breites Publikum. Teuer in der Produktion, lohnt "
                              "erst, wenn die günstigeren Kanäle ausgereizt sind.",
    "channel.video_ads.first_step": "Erst ein organisches Video machen, das nachweislich "
                                    "funktioniert, und genau dieses bewerben.",
    "channel.video_ads.risk": "Ohne vorhandenes Video ist das kein Kanal, sondern ein "
                              "Produktionsauftrag.",

    "channel.sponsoring.name": "Sponsoring in Verteilern und Podcasts",
    "channel.sponsoring.what": "Ein Platz in etwas, das die Zielgruppe freiwillig liest. Feste "
                               "Preise, kein Bieten, und die Erwähnung wirkt persönlich.",
    "channel.sponsoring.first_step": "Die drei Verteiler heraussuchen, die die Zielgruppe "
                                     "tatsächlich liest, und nach Mediadaten fragen.",
    "channel.sponsoring.risk": "Einmalige Platzierungen verpuffen. Erst die dritte Erwähnung wirkt.",

    # -- Werbemittel ---------------------------------------------------------
    "asset.seo_meta.name": "Titel und Meta-Beschreibung",
    "asset.seo_meta.what": "Was in der Trefferliste von Google steht. Der billigste Hebel "
                           "überhaupt - jeder andere Kanal führt hierher.",
    "asset.seo_meta.field.title": "Seitentitel",
    "asset.seo_meta.hint.title": "Google schneidet Längeres ab. Nutzen vor Markenname.",
    "asset.seo_meta.field.description": "Meta-Beschreibung",
    "asset.seo_meta.hint.description": "Kein Rankingfaktor, aber sie entscheidet über den Klick.",
    "asset.seo_meta.field.og_title": "Titel beim Teilen",
    "asset.seo_meta.hint.og_title": "Was in Discord, Slack und sozialen Netzen als Vorschau "
                                    "erscheint.",
    "asset.seo_meta.field.og_description": "Beschreibung beim Teilen",
    "asset.seo_meta.hint.og_description": "Kürzer als die Meta-Beschreibung - Vorschaukarten sind "
                                          "eng.",

    "asset.directory_listing.name": "Portal- und Verzeichniseintrag",
    "asset.directory_listing.what": "Für AlternativeTo, Product Hunt, Softpedia, Download-Portale, "
                                    "itch.io. Jedes Portal will eine andere Länge - deshalb alle "
                                    "drei.",
    "asset.directory_listing.field.tagline": "Einzeiler",
    "asset.directory_listing.hint.tagline": "Die Zeile direkt unter dem Namen.",
    "asset.directory_listing.field.short": "Kurzbeschreibung",
    "asset.directory_listing.hint.short": "Der übliche Umfang in Verzeichnissen.",
    "asset.directory_listing.field.long": "Ausführliche Beschreibung",
    "asset.directory_listing.hint.long": "Für Portale mit eigener Produktseite.",

    "asset.own_channel_post.name": "Ankündigung für eigene Kanäle",
    "asset.own_channel_post.what": "Discord und Mastodon. Diese Texte gehen als einzige "
                                   "vollautomatisch raus - es sind deine Kanäle.",
    "asset.own_channel_post.field.discord": "Discord",
    "asset.own_channel_post.hint.discord": "Formatierung mit ** und * ist erlaubt.",
    "asset.own_channel_post.field.mastodon": "Mastodon",
    "asset.own_channel_post.hint.mastodon": "Die meisten Instanzen erlauben 500 Zeichen.",

    "asset.google_search_ads.name": "Google-Suchanzeigen",
    "asset.google_search_ads.what": "Responsive Suchanzeige: Google mischt Überschriften und "
                                    "Beschreibungen selbst. Je mehr Varianten, desto mehr hat der "
                                    "Algorithmus zu kombinieren.",
    "asset.google_search_ads.note": "Ohne auszuschließende Suchbegriffe verbrennt jede "
                                    "Suchkampagne Geld an Anfragen, die nichts mit dem Produkt zu "
                                    "tun haben. Die Liste unten ist ein Anfang, kein Ersatz für "
                                    "den Suchbegriffsbericht nach zwei Wochen.",
    "asset.google_search_ads.field.headlines": "Überschriften",
    "asset.google_search_ads.hint.headlines": "Google will mindestens 3, empfiehlt 15. Jede muss "
                                              "allein stehen können.",
    "asset.google_search_ads.field.descriptions": "Beschreibungen",
    "asset.google_search_ads.hint.descriptions": "Mindestens 2, höchstens 4.",
    "asset.google_search_ads.field.paths": "Angezeigter Pfad",
    "asset.google_search_ads.hint.paths": "Kosmetik hinter der Domain, muss nicht existieren.",

    "asset.microsoft_ads.name": "Microsoft-Anzeigen (Bing)",
    "asset.microsoft_ads.what": "Dieselben Zeichengrenzen wie bei Google. Microsoft bietet den "
                                "Import der Google-Kampagne ausdrücklich an - das ist der "
                                "schnellere Weg.",
    "asset.microsoft_ads.field.headlines": "Überschriften",
    "asset.microsoft_ads.hint.headlines": "Wie bei Google.",
    "asset.microsoft_ads.field.descriptions": "Beschreibungen",
    "asset.microsoft_ads.hint.descriptions": "Wie bei Google.",

    "asset.meta_ads.name": "Meta-Anzeigen (Facebook, Instagram)",
    "asset.meta_ads.what": "Der Text trägt hier weniger als das Bild. Diese Zeilen sind das, was "
                           "neben dem Bild steht - ohne Bild ist keine davon etwas wert.",
    "asset.meta_ads.note": "Fachpublikum reagiert hier kaum. Bei Entwicklerwerkzeugen ist das Geld "
                           "meist verloren, bevor die erste Anzeige gelernt hat.",
    "asset.meta_ads.field.primary_text": "Primärtext",
    "asset.meta_ads.hint.primary_text": "Länger ist erlaubt, wird aber nach 125 Zeichen "
                                        "abgeschnitten.",
    "asset.meta_ads.field.headline": "Überschrift",
    "asset.meta_ads.hint.headline": "Steht fett unter dem Bild.",
    "asset.meta_ads.field.description": "Beschreibung",
    "asset.meta_ads.hint.description": "Wird nicht in jeder Platzierung angezeigt.",

    "asset.reddit_ads.name": "Reddit-Anzeigen",
    "asset.reddit_ads.what": "Der ehrliche Weg in Communities, in denen Eigenwerbung als Beitrag "
                             "verboten ist. Der Text muss klingen wie ein Beitrag, nicht wie ein "
                             "Prospekt.",
    "asset.reddit_ads.note": "Reddit-Nutzer erkennen Werbesprache sofort. Keine Superlative, keine "
                             "Ausrufezeichen - sonst wird die Anzeige nicht ignoriert, sondern "
                             "verspottet.",
    "asset.reddit_ads.field.headline": "Überschrift",
    "asset.reddit_ads.hint.headline": "Technisch sind 300 erlaubt. Über 100 liest sie niemand.",
    "asset.reddit_ads.field.body": "Fließtext",
    "asset.reddit_ads.hint.body": "Nur bei manchen Anzeigenformaten sichtbar.",

    "asset.store_listing.name": "Store-Eintrag",
    "asset.store_listing.what": "App Store, Google Play und Steam. Der Eintrag selbst ist der Kanal.",
    "asset.store_listing.field.app_name": "Name im Store",
    "asset.store_listing.hint.app_name": "App Store und Play erlauben beide 30.",
    "asset.store_listing.field.subtitle": "Untertitel",
    "asset.store_listing.hint.subtitle": "App Store. Wird mitdurchsucht.",
    "asset.store_listing.field.short_description": "Kurzbeschreibung",
    "asset.store_listing.hint.short_description": "Google Play. Steht ganz oben.",
    "asset.store_listing.field.steam_short": "Steam-Kurzbeschreibung",
    "asset.store_listing.hint.steam_short": "Steam. Erscheint in der Bibliothek und in der Suche.",
    "asset.store_listing.field.full_description": "Vollständige Beschreibung",
    "asset.store_listing.hint.full_description": "Play und App Store.",
    "asset.store_listing.field.keywords": "Suchbegriffe",
    "asset.store_listing.hint.keywords": "App Store, komma-getrennt, ohne Leerzeichen nach dem "
                                         "Komma.",

    "asset.press_kit.name": "Presse-Kit",
    "asset.press_kit.what": "Was eine Redaktion braucht, um ohne Rückfrage schreiben zu können. "
                            "Einzeln verschicken - Rundmails verbrennen den Kontakt dauerhaft.",
    "asset.press_kit.field.headline": "Meldungskopf",
    "asset.press_kit.hint.headline": "Was passiert ist, nicht wie toll es ist.",
    "asset.press_kit.field.lead": "Vorspann",
    "asset.press_kit.hint.lead": "Wer, was, wann, wo, warum - in einem Absatz.",
    "asset.press_kit.field.body": "Meldungstext",
    "asset.press_kit.hint.body": "Das Wichtigste zuerst. Redaktionen kürzen von unten.",
    "asset.press_kit.field.boilerplate": "Über das Projekt",
    "asset.press_kit.hint.boilerplate": "Der immer gleiche Absatz am Ende jeder Meldung.",
    "asset.press_kit.field.facts": "Fakten auf einen Blick",
    "asset.press_kit.hint.facts": "Preis, Plattformen, Version, Adresse.",

    # -- Presse-Texte --------------------------------------------------------
    "press.available_now": "{product} ist ab sofort verfügbar",
    "press.aimed_at": "Es richtet sich an {audience}.",
    "press.in_detail": "Im Einzelnen:",
    "press.fact.product": "Produkt",
    "press.fact.version": "Version",
    "press.fact.type": "Art",
    "press.fact.price": "Preis",
    "press.fact.regions": "Regionen",
    "press.fact.web": "Adresse",
    "listing.what_it_does": "Was es kann:",
    "listing.who_for": "Für wen:",
    "listing.pricing": "Preis:",
}

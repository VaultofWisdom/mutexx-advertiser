"""
Translation catalogue, interface shell: navigation, overview, dialogs and the
messages added with the 0.4 interface.

Same dictionary as i18n.py - kept in its own file so the long-form catalogue there
stays readable. Entries here override entries of the same name there.
"""

from __future__ import annotations

EN_UI: dict[str, str] = {
    # -- Navigation ----------------------------------------------------------
    "tab.overview": "Overview",
    "tab.legal": "Imprint & privacy",
    "page.legal.sub": "Who is behind the app, and what it does with data",
    "legal.imprint": "Imprint",
    "legal.privacy": "Privacy notice",
    "account.privacy_link": "Privacy notice",
    "nav.group.plan": "Plan",
    "nav.group.reach": "Reach",
    "nav.group.publish": "Publish",
    "nav.group.help": "Help & settings",
    "page.overview.sub": "Where this product stands, and what to do next",
    "page.product.sub": "Everything the tool does comes out of this profile",
    "page.analysis.sub": "What the product page says about the product",
    "page.strategy.sub": "Which channels are worth it - and which are not, and why",
    "page.assets.sub": "Finished copy, within each channel's character limits",
    "page.seeds.sub": "Where the scan starts looking",
    "page.communities.sub": "Found communities, their rules, and a verdict on each",
    "page.campaign.sub": "Prepared posts, spread over days - you send them",
    "page.channels.sub": "Your own channels - the only place the app posts by itself",
    "page.history.sub": "Everything that went out",
    "page.manual.sub": "The whole tool, explained",
    "page.settings.sub": "Keys, limits and language",
    "platform.forum": "Forum",
    "field.links.repo": "Links -> Repository",

    # -- Common --------------------------------------------------------------
    "action.confirm": "Confirm",
    "action.delete": "Delete",
    "common.all": "All",
    "common.today": "Today",
    "common.tomorrow": "Tomorrow",
    "common.unsaved": "Unsaved changes",
    "common.unsaved_title": "Discard unsaved changes?",
    "common.unsaved_body": "The product profile has changes that were not saved.",
    "common.discard": "Discard",

    # -- Overview ------------------------------------------------------------
    "overview.welcome_title": "Welcome to Mutexx Advertiser",
    "overview.welcome_body": "Describe your product. The tool reads its page, picks the "
                             "channels that suit it, finds communities whose rules allow it "
                             "and writes a post for each. It publishes nothing in other "
                             "people's communities - the last click stays yours.",
    "overview.welcome_step1": "Describe your product: a name, its page, one sentence.",
    "overview.welcome_step2": "Press Run everything - analysis, strategy, scan and copy in "
                              "one pass.",
    "overview.welcome_step3": "Work through the campaign. Every post is ready; you send it.",
    "overview.create_title": "Your first product",
    "overview.create": "Create product",
    "overview.name_ph": "Product name",
    "overview.no_one_liner": "No one-liner yet - add one in the product profile.",
    "overview.budget": "{amount} EUR budget per month",
    "overview.no_budget": "No budget - organic only",
    "overview.use_ai": "use AI (Anthropic key on file)",
    "overview.no_ai": "Without an Anthropic key the run works from templates. Add one under "
                      "Settings for AI analysis and copy.",
    "overview.next": "Next step",
    "overview.kpi.communities": "Communities",
    "overview.kpi.green": "{count} with no promotion ban",
    "overview.kpi.queue": "Prepared posts",
    "overview.kpi.queue_today": "{count} due today",
    "overview.kpi.posted": "Posted",
    "overview.kpi.posted_week": "{count} in the last 7 days",
    "overview.kpi.assets": "Assets",
    "overview.kpi.assets_of": "of {total} available",
    "overview.safety_title": "The last click stays with you",
    "overview.safety_body": "Fully automatic only in your own channels. In other people's "
                            "communities the app prepares everything and you send it - that "
                            "is what keeps a campaign from ending in a banned domain.",
    "overview.safety_today": "Manual posts in the last 24 hours: {count} of {limit}",
    "overview.last_run": "Last run",
    "overview.no_run_yet": "No full run in this session yet. Run everything walks analysis, "
                           "strategy, seed lists, scan, copy and campaign in one pass.",
    "step.product.done": "complete",
    "step.product.todo": "URL or one-liner missing",
    "step.analysis.done": "{count} keywords",
    "step.strategy.done": "{count} channels",
    "step.assets.done": "{count} written",
    "step.seeds.done": "{count} entries",
    "step.seeds.todo": "optional",
    "step.communities.done": "{count} found",
    "step.campaign.done": "{count} prepared",
    "step.todo": "not yet",
    "next.product": "Complete the product profile - the URL and the one-liner are what "
                    "everything else is built from.",
    "next.run": "Everything is in place for a first run. It takes a few minutes and "
                "publishes nothing.",
    "next.campaign": "Communities are rated. Prepare the campaign to get a draft for every "
                     "suitable one.",
    "next.post": "{count} prepared posts are due. Start posting mode and work through them.",
    "next.seeds": "Add forums to the seed lists - without them the scan covers Lemmy, "
                  "Hacker News and Lobsters only (and Reddit, once approved).",
    "next.done": "Nothing due right now. The next post is scheduled for {date}.",
    "next.rescan": "The campaign is through. Scan again in a few weeks - communities and "
                   "their rules change.",
    "next.go": "Go there",

    # -- Product -------------------------------------------------------------
    "product.section.identity": "Identity",
    "product.section.market": "Market and budget",
    "product.section.market_sub": "Who it is for and what it costs - this decides which "
                                  "channels the strategy even considers.",
    "product.section.text": "Description and keywords",
    "product.section.links": "Links",
    "product.saved": "Profile saved.",
    "product.deleted": "Product deleted.",

    # -- Analysis / strategy / assets ----------------------------------------
    "analysis.empty_title": "No analysis yet",
    "analysis.words_label": "words on the page",
    "strategy.empty_title": "No strategy yet",
    "strategy.phases": "Phases",
    "strategy.built": "Strategy rebuilt.",
    "assets.build_all": "Generate all recommended",
    "assets.all_done": "{count} assets generated.",
    "assets.ready": "ready",

    # -- Seeds ---------------------------------------------------------------
    "seeds.saved": "Seed lists saved.",

    # -- Communities ---------------------------------------------------------
    "communities.empty_title": "No communities yet",
    "communities.no_match": "Nothing matches this filter.",
    "communities.pick": "Pick a community on the left to see its rules, the verdict and a "
                        "ready draft.",
    "communities.add_hint": "Paste the community's rules - the verdict is computed from them "
                            "exactly as for scanned ones.",
    "communities.members_short": "members",
    "communities.per_day": "posts per day",
    "communities.score": "score",
    "communities.draft_hint": "Choose an angle and generate a draft.",
    "communities.pasted_rules": "Pasted rules",

    # -- Campaign ------------------------------------------------------------
    "campaign.title": "Campaign",
    "campaign.mode_hint": "Prepare drafts for every suitable community, spread over days by "
                          "the safety catch. Posting mode then walks you through them one at "
                          "a time: copy, open the form, send, next.",
    "campaign.empty_title": "No campaign yet",
    "campaign.group_count": "{count} posts",
    "campaign.counter": "Post {current} of {total}",
    "campaign.post_this": "Post this one",

    # -- Owned channels ------------------------------------------------------
    "channels.masked_note": "A webhook URL is a password: whoever has it can post as your "
                            "server. The interface only ever shows it masked.",
    "channels.mastodon_sub": "Your own account. Create a token under Preferences -> "
                             "Development with the write:statuses scope.",
    "channels.test_title": "Publish to your own channels",
    "channels.test_sub": "Sends the current draft - or, without one, a short product "
                         "announcement - to every channel above. This is real and public.",
    "channels.test_confirm_title": "Publish a real post?",
    "channels.test_confirm": "This publishes a public post to {count} owned channel(s) "
                             "right now: {channels}.",
    "channels.publish_now": "Publish now",
    "channels.hook_added": "Webhook added.",
    "channels.remove_hook": "Remove this webhook?",
    "channels.saved": "Mastodon saved.",
    "channels.mastodon_missing": "Mastodon is not configured.",

    # -- History -------------------------------------------------------------
    "history.count": "{count} entries",
    "history.empty_body": "Posts you mark as sent, and everything the owned channels "
                          "publish, are recorded here - the safety catch counts against it.",
    "history.result.posted": "posted by hand",
    "history.result.sent": "sent automatically",
    "history.result.failed": "failed (HTTP {status})",

    # -- Manual / settings ---------------------------------------------------
    "manual.contents": "Contents",
    "settings.data": "Data and privacy",
    "settings.data_dir": "Data folder",
    "settings.data_note": "Configuration, keys and campaign data live in this folder, on this "
                          "computer only. Nothing is sent anywhere except to the services you "
                          "use. No account, no telemetry.",
    "settings.model_hint": "Default and recommended: claude-opus-5-5.",
    "settings.safety_sub": "Holds the pace of posts into other people's communities. Several "
                           "on one day is exactly the pattern that reads as spam.",
    "settings.max_per_day": "Max. manual posts per day (Reddit, Lemmy, Hacker News and "
                            "Lobsters together)",
    "settings.secret_stored": "stored - type to replace",
    "settings.secret_remove": "Remove",
    "settings.secret_remove_title": "Remove this stored key?",
    "settings.secret_removed": "Removed.",
    "settings.saved": "Settings saved.",
    "settings.reddit_hint": "Reddit's API needs <b>explicit approval</b> before any access - "
                            "request it through Reddit's developer form first. Once approved: "
                            "on reddit.com/prefs/apps create an app of type <b>script</b>, "
                            "redirect uri <b>http://localhost:8777</b>. The client ID is printed "
                            "small <i>underneath</i> the app name. Read-only. Without approval "
                            "everything else works, and subreddits can be added by hand.",

    # -- Guard (wording widened: the limit covers every manual network) -------
    "guard.daily_limit": "Daily limit reached: {count} manual posts already went out in the "
                         "last 24 hours (limit {limit}). Several communities on one day is "
                         "exactly the pattern that reads as spam.",

    # -- Scan progress -------------------------------------------------------
    "scan.step.reddit_search": "Reddit search: {keyword}",
    "scan.step.reddit_candidates": "{count} subreddit candidates found - loading their details",
    "scan.step.reddit_about": "Details for r/{name}",
    "scan.step.reddit_neighbour": "Neighbouring subreddit r/{name}",
    "scan.step.rules": "Rules and activity: {name}",
    "scan.step.forum": "Checking forum: {name}",
    "scan.step.forum_new": "Checking a newly found forum: {name}",
    "scan.step.lemmy_search": "Lemmy search on {host}: {keyword}",
    "scan.step.hackernews": "Hacker News: rules and the topic's record",
    "scan.step.lobsters": "Lobsters: rules and matching tags",

    # -- Mutexx account ------------------------------------------------------
    "account.title": "Mutexx account",
    "account.optional": "optional",
    "account.local_only": "not signed in - everything stays local",
    "account.pitch": "One account for all Mutexx apps. Signed in, your products and "
                     "campaigns sync between your computers - including the history the "
                     "safety catch counts against, so a second machine never proposes a "
                     "community you posted to yesterday.",
    "account.never_synced": "Never synced: API keys, the Reddit secret, the Mastodon token "
                            "and Discord webhooks. They stay on this computer.",
    "account.display_name": "Display name",
    "account.email": "E-mail",
    "account.password": "Password",
    "account.sign_in": "Sign in",
    "account.create": "Create account",
    "account.no_account": "No account yet? Create one",
    "account.have_one": "Already have one? Sign in",
    "account.welcome": "Signed in. Syncing ...",
    "account.check_inbox": "Almost there - confirm the e-mail sent to {email}, then sign in.",
    "account.connected": "connected",
    "account.what_syncs": "Product profiles, seed lists, analysis, strategy, assets, "
                          "communities, campaign and history sync in the background every "
                          "few minutes. Keys and passwords never leave this computer.",
    "account.signed_in_as": "signed in as",
    "account.this_device": "this device",
    "account.sync_now": "Sync now",
    "account.syncing": "syncing ...",
    "account.synced_short": "sync on",
    "account.never": "Not synced yet.",
    "account.last_ok": "Last sync {when}: {pulled} received, {pushed} sent.",
    "account.conflicts": "{count} edited on two devices at once - the other device's "
                         "version was kept, yours is saved under data/account/conflicts.",
    "account.last_offline": "Last attempt {when}: no connection. Changes stay here and go "
                            "out with the next sync.",
    "account.last_error": "Last attempt {when} failed: {error}",
    "account.sign_out": "Sign out",
    "account.sign_out_title": "Sign out of the Mutexx account?",
    "account.sign_out_body": "Your data stays on this computer. It just stops syncing.",
    "account.signed_out": "Signed out.",
    "account.missing_fields": "E-mail and password, please.",
    "account.password_short": "The password needs at least 8 characters.",
    "account.wrong_credentials": "E-mail or password is not right.",
    "account.not_confirmed": "This account's e-mail address is not confirmed yet - look for "
                             "the confirmation e-mail.",
    "account.signup_failed": "The account could not be created: {error}",
    "account.not_signed_in": "Not signed in.",
    "account.expired": "The session has expired - please sign in again.",
    "account.unauthorized": "The account server refused the request - please sign in again.",
    "account.offline": "No connection to the account server ({error}).",
    "account.failed": "Sync failed: {error}",

    # -- Errors --------------------------------------------------------------
    "error.network": "No connection to the app. Is the window with the server still open?",
    "error.forbidden_origin": "Refused: the request did not come from this app's own page.",
    "error.webhook_url": "A webhook URL starts with https://",
    "error.api_refused": "The model declined this request.",
    "error.api_truncated": "The model's answer was cut off before the JSON was complete.",

    # -- Reddit --------------------------------------------------------------
    "reddit.no_credentials": "No Reddit API access on file. Reddit answers requests without "
                             "an approved, registered app with 403. Request access, create an "
                             "app of type 'script' at reddit.com/prefs/apps and put the client "
                             "ID and secret into Settings.",
    "reddit.no_token": "Reddit issued no token. Details: {details}",
    "reddit.no_token_need_bot": "Reddit issued no token. For script apps Reddit now usually "
                                "requires a separate bot account: create one, add it as a "
                                "developer of the app under prefs/apps and enter it here under "
                                "'Bot account'. Details: {details}",
    "reddit.no_token_check": "Reddit issued no token. Check the client ID (the small print "
                             "UNDER the app name), the secret, and whether the bot account is "
                             "listed as a developer of the app. With two-factor sign-in the "
                             "password goes in as 'password:2facode'. Details: {details}",
    "reddit.no_read_access": "Token received, but no read access. Check that the app type is "
                             "'script'.",
    "reddit.connected": "Connected to the Reddit API (method: {mode}).",
}


DE_UI: dict[str, str] = {
    "tab.overview": "Übersicht",
    "tab.legal": "Impressum & Datenschutz",
    "page.legal.sub": "Wer hinter der App steht, und was sie mit Daten macht",
    "legal.imprint": "Impressum",
    "legal.privacy": "Datenschutzhinweise",
    "account.privacy_link": "Datenschutzhinweise",
    "nav.group.plan": "Planen",
    "nav.group.reach": "Reichweite",
    "nav.group.publish": "Veröffentlichen",
    "nav.group.help": "Hilfe & Einstellungen",
    "page.overview.sub": "Wo dieses Produkt steht - und was als Nächstes zu tun ist",
    "page.product.sub": "Alles, was das Werkzeug tut, kommt aus diesem Profil",
    "page.analysis.sub": "Was die Produktseite über das Produkt sagt",
    "page.strategy.sub": "Welche Kanäle sich lohnen - welche nicht, und warum",
    "page.assets.sub": "Fertige Texte, innerhalb der Zeichengrenzen jedes Kanals",
    "page.seeds.sub": "Wo der Scan zu suchen beginnt",
    "page.communities.sub": "Gefundene Communities, ihre Regeln und ein Urteil zu jeder",
    "page.campaign.sub": "Vorbereitete Beiträge, über Tage verteilt - abschicken tust du",
    "page.channels.sub": "Deine eigenen Kanäle - der einzige Ort, an dem die App selbst postet",
    "page.history.sub": "Alles, was rausging",
    "page.manual.sub": "Das ganze Werkzeug, erklärt",
    "page.settings.sub": "Schlüssel, Grenzen und Sprache",
    "platform.forum": "Forum",
    "field.links.repo": "Links -> Repository",

    "action.confirm": "Bestätigen",
    "action.delete": "Löschen",
    "common.all": "Alle",
    "common.today": "Heute",
    "common.tomorrow": "Morgen",
    "common.unsaved": "Ungespeicherte Änderungen",
    "common.unsaved_title": "Ungespeicherte Änderungen verwerfen?",
    "common.unsaved_body": "Das Produktprofil hat Änderungen, die nicht gespeichert wurden.",
    "common.discard": "Verwerfen",

    "overview.welcome_title": "Willkommen beim Mutexx Advertiser",
    "overview.welcome_body": "Beschreibe dein Produkt. Das Werkzeug liest seine Seite, wählt "
                             "die Kanäle, die dazu passen, findet Communities, deren Regeln es "
                             "erlauben, und schreibt für jede einen Beitrag. In fremden "
                             "Communities veröffentlicht es nichts - der letzte Klick bleibt "
                             "bei dir.",
    "overview.welcome_step1": "Beschreibe dein Produkt: Name, Seite, ein Satz.",
    "overview.welcome_step2": "Drücke „Alles durchlaufen lassen“ - Analyse, Strategie, Scan "
                              "und Texte in einem Durchgang.",
    "overview.welcome_step3": "Arbeite die Kampagne ab. Jeder Beitrag ist fertig; abschicken "
                              "tust du.",
    "overview.create_title": "Dein erstes Produkt",
    "overview.create": "Produkt anlegen",
    "overview.name_ph": "Produktname",
    "overview.no_one_liner": "Noch kein Einzeiler - im Produktprofil ergänzen.",
    "overview.budget": "{amount} EUR Budget im Monat",
    "overview.no_budget": "Kein Budget - nur organisch",
    "overview.use_ai": "KI verwenden (Anthropic-Schlüssel hinterlegt)",
    "overview.no_ai": "Ohne Anthropic-Schlüssel arbeitet der Durchlauf mit Vorlagen. Unter "
                      "Einstellungen einen hinterlegen für KI-Analyse und -Texte.",
    "overview.next": "Nächster Schritt",
    "overview.kpi.communities": "Communities",
    "overview.kpi.green": "{count} ohne Werbeverbot",
    "overview.kpi.queue": "Vorbereitete Beiträge",
    "overview.kpi.queue_today": "{count} heute fällig",
    "overview.kpi.posted": "Gepostet",
    "overview.kpi.posted_week": "{count} in den letzten 7 Tagen",
    "overview.kpi.assets": "Werbemittel",
    "overview.kpi.assets_of": "von {total} möglichen",
    "overview.safety_title": "Der letzte Klick bleibt bei dir",
    "overview.safety_body": "Vollautomatisch nur in deinen eigenen Kanälen. In fremden "
                            "Communities bereitet die App alles vor und du schickst es ab - "
                            "genau das bewahrt eine Kampagne davor, in einer gesperrten Domain "
                            "zu enden.",
    "overview.safety_today": "Manuelle Beiträge in den letzten 24 Stunden: {count} von {limit}",
    "overview.last_run": "Letzter Durchlauf",
    "overview.no_run_yet": "In dieser Sitzung noch kein kompletter Durchlauf. „Alles "
                           "durchlaufen lassen“ geht Analyse, Strategie, Startlisten, Scan, "
                           "Texte und Kampagne in einem Durchgang ab.",
    "step.product.done": "vollständig",
    "step.product.todo": "URL oder Einzeiler fehlt",
    "step.analysis.done": "{count} Stichwörter",
    "step.strategy.done": "{count} Kanäle",
    "step.assets.done": "{count} geschrieben",
    "step.seeds.done": "{count} Einträge",
    "step.seeds.todo": "optional",
    "step.communities.done": "{count} gefunden",
    "step.campaign.done": "{count} vorbereitet",
    "step.todo": "noch nicht",
    "next.product": "Produktprofil vervollständigen - URL und Einzeiler sind das, worauf alles "
                    "andere aufbaut.",
    "next.run": "Alles bereit für einen ersten Durchlauf. Er dauert ein paar Minuten und "
                "veröffentlicht nichts.",
    "next.campaign": "Die Communities sind bewertet. Bereite die Kampagne vor, um für jede "
                     "geeignete einen Entwurf zu bekommen.",
    "next.post": "{count} vorbereitete Beiträge sind fällig. Starte den Posting-Modus und "
                 "arbeite sie ab.",
    "next.seeds": "Trag Foren in die Startlisten ein - ohne sie deckt der Scan nur Lemmy, "
                  "Hacker News und Lobsters ab (und Reddit, sobald freigegeben).",
    "next.done": "Gerade ist nichts fällig. Der nächste Beitrag ist für {date} geplant.",
    "next.rescan": "Die Kampagne ist durch. In ein paar Wochen erneut scannen - Communities "
                   "und ihre Regeln ändern sich.",
    "next.go": "Hingehen",

    "product.section.identity": "Identität",
    "product.section.market": "Markt und Budget",
    "product.section.market_sub": "Für wen es ist und was es kostet - das entscheidet, welche "
                                  "Kanäle die Strategie überhaupt in Betracht zieht.",
    "product.section.text": "Beschreibung und Stichwörter",
    "product.section.links": "Links",
    "product.saved": "Profil gespeichert.",
    "product.deleted": "Produkt gelöscht.",

    "analysis.empty_title": "Noch keine Analyse",
    "analysis.words_label": "Wörter auf der Seite",
    "strategy.empty_title": "Noch keine Strategie",
    "strategy.phases": "Phasen",
    "strategy.built": "Strategie neu erstellt.",
    "assets.build_all": "Alle empfohlenen erzeugen",
    "assets.all_done": "{count} Werbemittel erzeugt.",
    "assets.ready": "fertig",

    "seeds.saved": "Startlisten gespeichert.",

    "communities.empty_title": "Noch keine Communities",
    "communities.no_match": "Nichts passt zu diesem Filter.",
    "communities.pick": "Wähle links eine Community, um ihre Regeln, das Urteil und einen "
                        "fertigen Entwurf zu sehen.",
    "communities.add_hint": "Füge die Regeln der Community ein - das Urteil wird daraus genauso "
                            "berechnet wie bei gescannten.",
    "communities.members_short": "Mitglieder",
    "communities.per_day": "Beiträge pro Tag",
    "communities.score": "Punkte",
    "communities.draft_hint": "Blickwinkel wählen und einen Entwurf erzeugen.",
    "communities.pasted_rules": "Eingefügte Regeln",

    "campaign.title": "Kampagne",
    "campaign.mode_hint": "Entwürfe für jede geeignete Community vorbereiten, vom "
                          "Schutzschalter über Tage verteilt. Der Posting-Modus führt dann "
                          "einzeln durch: kopieren, Formular öffnen, abschicken, weiter.",
    "campaign.empty_title": "Noch keine Kampagne",
    "campaign.group_count": "{count} Beiträge",
    "campaign.counter": "Beitrag {current} von {total}",
    "campaign.post_this": "Diesen posten",

    "channels.masked_note": "Eine Webhook-URL ist ein Passwort: Wer sie hat, kann als dein "
                            "Server posten. Die Oberfläche zeigt sie nur maskiert.",
    "channels.mastodon_sub": "Dein eigenes Konto. Token unter Einstellungen -> Entwicklung "
                             "mit dem Recht write:statuses anlegen.",
    "channels.test_title": "In eigene Kanäle veröffentlichen",
    "channels.test_sub": "Schickt den aktuellen Entwurf - oder ohne einen eine kurze "
                         "Produktankündigung - an jeden Kanal oben. Das ist echt und "
                         "öffentlich.",
    "channels.test_confirm_title": "Echten Beitrag veröffentlichen?",
    "channels.test_confirm": "Das veröffentlicht jetzt einen öffentlichen Beitrag in "
                             "{count} eigene(n) Kanal/Kanäle: {channels}.",
    "channels.publish_now": "Jetzt veröffentlichen",
    "channels.hook_added": "Webhook hinzugefügt.",
    "channels.remove_hook": "Diesen Webhook entfernen?",
    "channels.saved": "Mastodon gespeichert.",
    "channels.mastodon_missing": "Mastodon ist nicht eingerichtet.",

    "history.count": "{count} Einträge",
    "history.empty_body": "Beiträge, die du als gesendet markierst, und alles, was die eigenen "
                          "Kanäle veröffentlichen, landen hier - der Schutzschalter zählt "
                          "dagegen.",
    "history.result.posted": "von Hand gepostet",
    "history.result.sent": "automatisch gesendet",
    "history.result.failed": "fehlgeschlagen (HTTP {status})",

    "manual.contents": "Inhalt",
    "settings.data": "Daten und Datenschutz",
    "settings.data_dir": "Datenordner",
    "settings.data_note": "Konfiguration, Schlüssel und Kampagnendaten liegen in diesem Ordner, "
                          "nur auf diesem Rechner. Nichts geht irgendwohin außer an die Dienste, "
                          "die du nutzt. Kein Konto, keine Telemetrie.",
    "settings.model_hint": "Voreinstellung und Empfehlung: claude-opus-5-5.",
    "settings.safety_sub": "Hält das Tempo der Beiträge in fremden Communities. Mehrere an einem "
                           "Tag sind genau das Muster, das als Spam gelesen wird.",
    "settings.max_per_day": "Max. manuelle Beiträge pro Tag (Reddit, Lemmy, Hacker News und "
                            "Lobsters zusammen)",
    "settings.secret_stored": "hinterlegt - zum Ersetzen neu eingeben",
    "settings.secret_remove": "Entfernen",
    "settings.secret_remove_title": "Diesen hinterlegten Schlüssel entfernen?",
    "settings.secret_removed": "Entfernt.",
    "settings.saved": "Einstellungen gespeichert.",
    "settings.reddit_hint": "Reddits API verlangt vor jedem Zugriff eine <b>ausdrückliche "
                            "Freigabe</b> - zuerst über Reddits Entwicklerformular beantragen. "
                            "Nach der Freigabe: auf reddit.com/prefs/apps eine App vom Typ "
                            "<b>script</b> anlegen, redirect uri <b>http://localhost:8777</b>. "
                            "Die Client-ID steht klein <i>unter</i> dem App-Namen. Nur "
                            "Lesezugriff. Ohne Freigabe funktioniert alles andere, und "
                            "Subreddits lassen sich von Hand aufnehmen.",

    "guard.daily_limit": "Tageslimit erreicht: in den letzten 24 Stunden gingen bereits {count} "
                         "manuelle Beiträge raus (Limit {limit}). Mehrere Communities am selben "
                         "Tag sind genau das Muster, das als Spam erkannt wird.",

    "scan.step.reddit_search": "Reddit-Suche: {keyword}",
    "scan.step.reddit_candidates": "{count} Subreddit-Kandidaten gefunden - lade Stammdaten",
    "scan.step.reddit_about": "Stammdaten r/{name}",
    "scan.step.reddit_neighbour": "Nachbar-Subreddit r/{name}",
    "scan.step.rules": "Regeln und Aktivität: {name}",
    "scan.step.forum": "Forum prüfen: {name}",
    "scan.step.forum_new": "Neu gefundenes Forum prüfen: {name}",
    "scan.step.lemmy_search": "Lemmy-Suche auf {host}: {keyword}",
    "scan.step.hackernews": "Hacker News: Regeln und Themenlage",
    "scan.step.lobsters": "Lobsters: Regeln und passende Tags",

    "account.title": "Mutexx Konto",
    "account.optional": "freiwillig",
    "account.local_only": "nicht angemeldet - alles bleibt lokal",
    "account.pitch": "Ein Konto für alle Mutexx-Apps. Angemeldet gleichen sich deine "
                     "Produkte und Kampagnen zwischen deinen Rechnern ab - auch der Verlauf, "
                     "gegen den der Schutzschalter zählt, damit ein zweiter Rechner nie eine "
                     "Community vorschlägt, in der du gestern gepostet hast.",
    "account.never_synced": "Nie abgeglichen: API-Schlüssel, Reddit-Secret, Mastodon-Token "
                            "und Discord-Webhooks. Sie bleiben auf diesem Rechner.",
    "account.display_name": "Anzeigename",
    "account.email": "E-Mail",
    "account.password": "Passwort",
    "account.sign_in": "Anmelden",
    "account.create": "Konto anlegen",
    "account.no_account": "Noch kein Konto? Jetzt anlegen",
    "account.have_one": "Schon ein Konto? Anmelden",
    "account.welcome": "Angemeldet. Abgleich läuft ...",
    "account.check_inbox": "Fast geschafft - bestätige die E-Mail an {email} und melde dich "
                           "dann an.",
    "account.connected": "verbunden",
    "account.what_syncs": "Produktprofile, Startlisten, Analyse, Strategie, Werbemittel, "
                          "Communities, Kampagne und Verlauf gleichen sich alle paar Minuten im "
                          "Hintergrund ab. Schlüssel und Passwörter verlassen diesen Rechner nie.",
    "account.signed_in_as": "angemeldet als",
    "account.this_device": "dieses Gerät",
    "account.sync_now": "Jetzt abgleichen",
    "account.syncing": "gleicht ab ...",
    "account.synced_short": "Abgleich an",
    "account.never": "Noch nicht abgeglichen.",
    "account.last_ok": "Letzter Abgleich {when}: {pulled} empfangen, {pushed} gesendet.",
    "account.conflicts": "{count} gleichzeitig auf zwei Geräten bearbeitet - die Fassung des "
                         "anderen Geräts gilt, deine liegt unter data/account/conflicts.",
    "account.last_offline": "Letzter Versuch {when}: keine Verbindung. Änderungen bleiben hier "
                            "und gehen mit dem nächsten Abgleich raus.",
    "account.last_error": "Letzter Versuch {when} fehlgeschlagen: {error}",
    "account.sign_out": "Abmelden",
    "account.sign_out_title": "Vom Mutexx Konto abmelden?",
    "account.sign_out_body": "Deine Daten bleiben auf diesem Rechner. Sie gleichen sich nur "
                             "nicht mehr ab.",
    "account.signed_out": "Abgemeldet.",
    "account.missing_fields": "Bitte E-Mail und Passwort angeben.",
    "account.password_short": "Das Passwort braucht mindestens 8 Zeichen.",
    "account.wrong_credentials": "E-Mail oder Passwort stimmt nicht.",
    "account.not_confirmed": "Die E-Mail-Adresse dieses Kontos ist noch nicht bestätigt - "
                             "bitte die Bestätigungsmail suchen.",
    "account.signup_failed": "Das Konto ließ sich nicht anlegen: {error}",
    "account.not_signed_in": "Nicht angemeldet.",
    "account.expired": "Die Sitzung ist abgelaufen - bitte neu anmelden.",
    "account.unauthorized": "Der Kontoserver hat die Anfrage abgelehnt - bitte neu anmelden.",
    "account.offline": "Keine Verbindung zum Kontoserver ({error}).",
    "account.failed": "Abgleich fehlgeschlagen: {error}",

    "error.network": "Keine Verbindung zur App. Ist das Fenster mit dem Server noch offen?",
    "error.forbidden_origin": "Abgelehnt: Die Anfrage kam nicht von der eigenen Seite der App.",
    "error.webhook_url": "Eine Webhook-URL beginnt mit https://",
    "error.api_refused": "Das Modell hat diese Anfrage abgelehnt.",
    "error.api_truncated": "Die Antwort des Modells brach ab, bevor das JSON vollständig war.",

    "reddit.no_credentials": "Kein Reddit-API-Zugang hinterlegt. Reddit beantwortet Anfragen "
                             "ohne freigegebene, registrierte App mit 403. Zugang beantragen, "
                             "unter reddit.com/prefs/apps eine App vom Typ 'script' anlegen und "
                             "Client-ID und Secret in den Einstellungen eintragen.",
    "reddit.no_token": "Reddit hat kein Token ausgestellt. Details: {details}",
    "reddit.no_token_need_bot": "Reddit hat kein Token ausgestellt. Für Script-Apps verlangt "
                                "Reddit inzwischen meist ein eigenes Bot-Konto: eines anlegen, "
                                "unter prefs/apps als Developer der App eintragen und hier unter "
                                "„Bot-Konto“ hinterlegen. Details: {details}",
    "reddit.no_token_check": "Reddit hat kein Token ausgestellt. Prüfe die Client-ID (klein "
                             "UNTER dem App-Namen), das Secret und ob das Bot-Konto als "
                             "Developer der App eingetragen ist. Bei Zwei-Faktor-Anmeldung wird "
                             "das Passwort als 'passwort:2facode' angegeben. Details: {details}",
    "reddit.no_read_access": "Token erhalten, aber kein Lesezugriff. Bitte App-Typ 'script' "
                             "prüfen.",
    "reddit.connected": "Verbindung zur Reddit-API steht (Verfahren: {mode}).",
}

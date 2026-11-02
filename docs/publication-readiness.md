# Publicatiegereedheid — WorkNew 0.4.0

Dit document scheidt voorbereide bestanden van platformacceptatie. Een geslaagde build is geen directorygoedkeuring. De werkende publieke uitleg staat op https://worknew.co/mcp. De openbare server is https://mcp.worknew.co/v1/mcp en vereist geen gebruikersauthenticatie.

## Voorbereide release

- Naam: **WorkNew**, pakketnaam **worknew-jobs**, versie **0.4.0**.
- Uitgever: **CreateNew Work B.V.**, expliciet bevestigd door de gebruiker. Licentie en pakketmetadata zijn hierop aangepast. De privacyverklaring noemt nog Design-Well B.V.; de rolverdeling in de publieke juridische informatie moet worden afgestemd. Het platform bepaalt de getoonde uitgever op basis van de geverifieerde identiteit.
- Licentie: proprietary; installatie en gebruik toegestaan. Geen toestemming voor wijziging of herdistributie. De gebruiker koos dit expliciet.
- GitHub-bron: `https://github.com/CreateNewCo/worknewjobs-plugin`, pluginpad de repositoryroot. Beide source-manifests en `.mcp.json` beschrijven de verbonden release; de builder verwijdert de verbinding alleen voor skills-only-pakketten.
- OpenAI-pakket: `dist/connected/worknew-jobs-chatgpt-0.4.0.zip` na een build.
- Claude-pakket: `dist/connected/worknew-jobs-claude-0.4.0.zip` na een build. De directory leest de GitHub-bron; een lokale ZIP is alleen voor testen of directe installatie.
- Vijf positieve en drie negatieve reviewcases staan in `.codex-plugin/plugin.json` onder `extensions.com.openai.review`. De builder neemt ze mee in de verbonden portable manifest. Dit zijn reproduceerbare acceptatie-instructies, geen claim dat hosttests zijn uitgevoerd.
- README, licentie, publieke website-/support-/privacy-/voorwaardenlinks en release notes worden meegeleverd.

## Bewijs en openstaande controles

| Onderdeel | Status / bewijs |
| --- | --- |
| Cloudflare en MCP | Live checker geslaagd op 2 november 2026, zonder aangepaste User-Agent: protocol 2025-11-25, search_jobs, 3 resultaten. Zie deployment-status.md. |
| Publieke uitleg | `https://worknew.co/mcp` in Chrome gelezen, inclusief installatie-instructies en supportcontact. |
| Privacy-URL | `https://worknew.co/legal/privacy` in Chrome gelezen; noemt Design-Well B.V. en support@worknew.co. MCP-specifieke gegevensverwerking en bewaartermijnen vragen nog controle. |
| Voorwaarden-URL | In Chrome volledig gelezen. Noemt CreateNew Work B.V., terwijl de privacyverklaring Design-Well B.V. noemt. De gebruiker heeft CreateNew Work B.V. als uitgever bevestigd; afstemming van de publieke juridische informatie staat nog open. |
| Branding | Officieel SVG opgehaald van de publieke WorkNew-site; komt byte-voor-byte overeen met het bestaande WordPress-themeasset. Met expliciete toestemming alleen width en height naar 512 × 512 aangepast; artwork ongewijzigd. |
| Lokale packagechecks | 18 Python-tests geslaagd, plus negen directe MCP-controles; zie verification-2026-11-02.json. Claude CLI 2.1.316 valideerde het connected pakket zonder directoryfindings. Definitieve assets en platformscans blijven afzonderlijk nodig. |
| OpenAI-/portable schema | plugin.json slaagt tegen het gepubliceerde Agent Plugins-schema. De MCP-kern slaagt zonder de OpenAI-extensie; het generieke MCP-schema weigert per-server extensions, terwijl de actuele OpenAI-documentatie de gebruikte auth-extensie expliciet voorschrijft. De gedocumenteerde auth-configuratie blijft behouden; portalvalidatie moet dit bevestigen. Schemas en hashes staan in het verificatiebestand. |
| GitHub-release | Repository is publiek. De nieuwe 0.4.0-bestanden moeten nog worden gepusht en teruggelezen. |
| ChatGPT-hosttest | Niet uitgevoerd. Test installatie, onboarding en alle reviewcases met de verbonden release. |
| Claude-hosttest | Niet uitgevoerd. Test installatie, onboarding en alle reviewcases met de verbonden release. |
| Video | Nog geen opgenomen en publiek/reviewer-bereikbaar walkthroughbestand. De uitlegpagina is geen video. |
| OpenAI-portal | Aangemeld bij CreateNew. Upload blokkeert op developer identity verification. Business Start vereist eerst een geldige standaardbetaalmethode; gebruiker gevraagd dit en verificatie zelf af te ronden. Nog geen draft of domeinchallenge. |
| Claude-portal | Aangemeld. Account is Free; de portal vereist een betaald plan voor directorysubmissions. Gebruiker gevraagd een betaald account te gebruiken of zelf te upgraden. Nog geen connector- of bundledraft. |

## OpenAI-draft voorbereiden

Gebruik https://platform.openai.com/plugins en **With MCP**. Upload de verbonden ZIP bij de organisatie die de listing moet bezitten. Selecteer de geverifieerde bedrijfsidentiteit. Controleer geïmporteerde velden en stel de serverauthenticatie in op geen authenticatie.

Host pas na ontvangst van de portalchallenge de exacte tekst op de getoonde `/.well-known/openai-apps-challenge`-URL. De bestaande Worker weigert andere paden; de challenge vraagt daarom mogelijk een afzonderlijke, exacte route of een toegestane parent-host. Maak geen brede uitzondering en vervang geen challenge van een andere plugin. Voer Verify Domain uit en controleer de tool- en skillscans.

Voeg de echte recording-URL toe aan `extensions.com.openai.review.demo_recording_url`, rebuild en upload opnieuw. Gebruik geen placeholder-URL. Toolannotaties en hun onderbouwing staan hieronder. Voltooi de platformattestaties pas wanneer de daadwerkelijke gegevensverwerking is bevestigd. Een draft indienen en publiceren zijn afzonderlijke acties.

## Claude-drafts voorbereiden

Gebruik https://claude.ai/directory/manage met een betaald account en de juiste organisatie. Maak eerst een **MCP connector** met de publieke server-URL, geen authenticatie, de gegevens in `claude-connector-listing.json` en de werkelijke testresultaten.

Maak daarna een **Plugin bundle** voor `CreateNewCo/worknewjobs-plugin`, de repositoryroot, op de gekozen releasebranch of tag. De gekoppelde GitHub-gebruiker moet pushrechten hebben. Voer Validate uit op de exacte releasecommit. Vul gegevensverwerking en support in, en koppel beide listings in dezelfde organisatie. Publiceer pas na de toepasselijke scans/review en expliciete publicatiebeslissing.

## Onderbouwing van toolannotaties

| Annotatie | Waarde | Onderbouwing |
| --- | --- | --- |
| readOnlyHint | true | search_jobs leest openbare opdrachten en retourneert resultaten; geen profielopslag, sollicitatie of wijziging. |
| destructiveHint | false | De tool verwijdert of wijzigt geen gebruikers- of opdrachtgegevens. |
| openWorldHint | false | De tool doorzoekt uitsluitend de gecontroleerde WorkNew-collectie; geen willekeurige URLs, vrij internetzoeken of interactie met externe ontvangers. |
| idempotentHint | true | Herhaling heeft geen zakelijke neveneffecten. Resultaten kunnen wijzigen door veranderend aanbod; rate-limitmeters tellen wel aanvragen. |

Controleer deze waarden opnieuw tegen de live toolscan voordat ze als attestatie worden ingediend.

## Actuele officiële instructies

- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/plugins/deploy/submission-errors
- https://claude.com/docs/directory/publish
- https://claude.com/docs/plugins/pre-submission-checklist
- https://claude.com/docs/connectors/building/submission

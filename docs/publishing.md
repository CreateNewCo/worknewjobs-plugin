# Publicatie en verificatie

## CURRENT STATE snapshot — 2 november 2026

De norm voor de zoekintegratie staat in [Backendintegratie — END STATE](backend-integration.md) en de [backendhandoff](backend-handoff.md). Versie 0.3.0 bouwt twee platformpakketten en levert skills, machineleesbare contracts en een MCP-checker. De backend is geïmplementeerd en Cloudflare is ingericht; zie de [uitrolstatus](deployment-status.md) voor resterende verificatie. Directorypublicatie is nog niet uitgevoerd.

De source-manifests verwijzen naar dezelfde skills. De build schrijft een Claude-pakket en een portable ChatGPT-pakket met expliciete onboarding. Een standaardbuild bevat de vaste publieke MCP-verbinding; `--skills-only` bevat geen verbinding. Er zijn geen installatiehooks of geregistreerde connectors. Zie de [OpenAI-verpakkingsdocumentatie](https://developers.openai.com/plugins/build/plugins).

## Concrete publicatiegaten

| Nog nodig | Gereed wanneer |
| --- | --- |
| Anonieme productieverbinding | Echte HTTPS-MCP-URL, begrensde aanvragen, veilige foutafhandeling en operationele logging geverifieerd |
| Branding | Officieel bronlogo, vierkant logo en icoon toegevoegd; manifestpaden werken |
| Publieke documentatie | Bereikbare pluginuitleg en HTTPS-supportpagina vastgesteld |
| Privacy en voorwaarden | Bestaande WorkNew-links gecontroleerd en zo nodig uitgebreid voor het echte gegevenspad |
| Platformidentiteit | Juridische ontwikkelaar/bedrijf en domeineigendom geverifieerd |
| Hostcontrole | Installatie, setup en echte zoekresultaten getest in Claude én ChatGPT |
| Reviewmateriaal | Demo, verwachte/werkelijke testresultaten en release notes beschikbaar |
| Directorypublicatie | Beide platformreviews afgerond en zichtbare listing gecontroleerd |

Deze punten zijn nog niet volledig afgerond. De productie-URL is https://mcp.worknew.co/v1/mcp. Een build of mocktest bewijst geen live MCP-bereikbaarheid. De buildreport vermeldt daarom altijd `backendVerified: false`.

## Platformroutes

### ChatGPT

1. Houd naam, korte tekst, lange tekst en drie prompts binnen de actuele directorylimieten: respectievelijk 30, 30, 4000 en 128 tekens per prompt. Voeg de echte logo- en icoonbestanden toe.
2. Dien de werkende remote server in via **With MCP**, met website-, support-, privacy- en voorwaarden-HTTPS-URL's. Een skills-only-upload vervangt deze koppeling niet.
3. Voltooi identiteit/domeincontrole, skill- en toolscans. Lever demo, release notes, vijf positieve en drie negatieve cases, plus toolannotaties met onderbouwing. OAuth-testcredentials zijn voor deze anonieme versie niet van toepassing.
4. Alleen bij custom UI: screenshots per starterprompt, 706 pixels breed en 400–860 hoog. Deze versie heeft geen custom UI.

Bron: [OpenAI-submissievoorwaarden](https://developers.openai.com/plugins/deploy/submission-errors). Hercontroleer bij publicatie; lokale validatie is geen directorygoedkeuring.

### Claude

Valideer eerst met `claude plugin validate . --strict` en test een installatie. Controleer daarna componentondersteuning in de beoogde Claude-oppervlakken en dien de GitHub-plugin in via [Anthropic's developerportal](https://claude.ai/directory/manage). Houd de eventuele connectorregistratie bij de remote server; een werkende Claude Code-sessie alleen bewijst geen werking in Claude chat. Volg de [officiële distributiehandleiding](https://code.claude.com/docs/en/plugins/publish) voor review en versie-updates.

Een eigen GitHub-marketplace is een afzonderlijke distributieroute, geen directorygoedkeuring. De build maakt geen marketplacecatalogus of publieke release aan. De source-manifests staan op `0.3.0`; verhoog beide samen bij een volgende release.

## Verificatie van de pluginpakketten

- Parseer beide manifests, de workspace en het MCP-voorbeeld als JSON; valideer de YAML-frontmatter van beide skills.
- Controleer alle componentpaden vanuit de pluginroot, inclusief onboarding, en alle lokale Markdown-links vanuit hun documentmap.
- Draai `python -m worknew_plugins validate` en `python -m unittest discover -s tests -v` in de ontwikkelomgeving. Controleer zowel een skills-only als een verbonden build; alleen de laatste mag een MCP-config bevatten.
- Draai `python -m worknew_plugins audit` voor bekende secretpatronen en private routes in publiceerbare bronbestanden. Dit is een gerichte regressiecheck, geen volledige security-audit. De build scant ook de verpakte bestanden en de publieke handoff.
- Controleer met `git check-ignore` dat persoonlijke testdata en secrets genegeerd worden en de workspace, manifests en skills niet.
- Voer waar beschikbaar `claude plugin validate . --strict` uit. Een ontbrekende CLI is een niet-uitgevoerde platformcheck, geen succesvolle validatie.

Er is geen gehoste backend in deze repository. Onderstaande scenario's zijn acceptatiecriteria; unit-/mocktests zijn geen host-run of live bewijs. Noteer bij echte uitvoering datum, host, versie, verwacht resultaat, werkelijk resultaat en bewijs zonder persoonlijke gegevens.

**Lokale verificatie op 27 oktober 2026:** bronvalidatie, publicatiescan en 15 testmethoden met meerdere grens-/foutscenario's geslaagd. Getest: deterministische ZIPs, allowlist van pakketbestanden, vaste publieke URL, blokkeren van andere productie-endpoints, input/outputrestricties, HTTP/JSON en SSE met een lokale mockserver, sessieheaders, toolpaginering en veilige foutafhandeling. De onboardinginstructies zijn gereviewd. Claude CLI was niet geïnstalleerd; officiële platformvalidatie, setup in beide hosts en live backendtests blijven open. De GitHub Actions-workflow voert dezelfde checks uit zodra de repository wordt gepusht; er is hier geen CI-run geclaimd.

## Onboardingreview

| Scenario | Verwacht gedrag |
| --- | --- |
| Cv al aanwezig | Hergebruik rollen/vaardigheden; vraag niet opnieuw om hetzelfde cv en verstuur geen identiteit of cv-tekst |
| Cv geweigerd | Accepteer dit direct en vraag naar gewenste rollen |
| Voorkeuren al genoemd | Vat samen en vraag alleen naar relevante ontbrekende informatie; cv is geen vereiste |
| Cv onleesbaar | Leg leesprobleem uit en bied rolvoorkeuren of een vrijwillige samenvatting aan |
| Setup gestart in nieuw/bestaand gesprek | De verpakte get-started-skill wordt geladen; bestaande context wordt hergebruikt |

## Zoekreview voor de toekomstige release

De eerste vijf cases zijn positief; de laatste drie zijn negatief. Gebruik synthetische voorkeuren, gecontroleerde backendfixtures voor lege resultaten en paginering, en een aparte live rooktest met actuele openbare opdrachten. Presenteer fixtures nooit als echte vacatures.

| Case | Scenario | Verwacht gedrag |
| --- | --- | --- |
| P1 | Rol plus expliciete voorkeuren, zonder cv | Alleen ondersteunde inputs; openbare resultaten en echte WorkNew-links |
| P2 | Vrijwillig cv met rollen/vaardigheden | Alleen zoektermen/filters naar de tool; geen cv-upload, naam of contactgegevens |
| P3 | Succesvolle zoekopdracht zonder matches | Eerlijke nulmelding en een voorstel tot verruiming |
| P4 | Volgende pagina gevraagd | Zelfde filters, `nextOffset` gebruiken; bij nieuwe filters opnieuw vanaf nul |
| P5 | Redacted opdracht met ontbrekende velden | Redactie behouden, onbekende waarden benoemen, geen private reconstructie |
| N1 | Connector ontbreekt | Uitleg dat live zoeken niet is aangesloten; geen fictieve resultaten of tokenvraag |
| N2 | Backend/transport faalt | Fout onderscheiden van nul matches; geen credentiallek of eindeloze retries |
| N3 | Gebruiker vraagt te solliciteren | Geen mutatie of upload; beperking uitleggen en beschikbare WorkNew-link tonen |

Voor N2 moeten backendtests ook ongeldige invoer, onverwachte respons, time-out en pogingen tot `scope`/`personId`-overrides afdekken. Doe live tests pas na de implementatie en publiceer pas wanneer de openstaande punten aantoonbaar zijn afgehandeld.

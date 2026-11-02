# Publicatie en verificatie

De release **0.4.0** wordt voorbereid voor de publieke ChatGPT- en Claude-directories. Zie [publicatiegereedheid](publication-readiness.md) voor het actuele bewijs en de resterende platformstappen. De openbare MCP-verbinding werkt via Cloudflare; de [uitrolstatus](deployment-status.md) beschrijft de live verificatie.

## Pakketten bouwen en controleren

```sh
.venv/bin/python -m worknew_plugins validate
.venv/bin/python -m worknew_plugins audit
.venv/bin/python -m worknew_plugins check-publication
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m worknew_plugins build --skills-only
.venv/bin/python -m worknew_plugins build
npx --yes @anthropic-ai/claude-code@2.1.316 plugin validate . --strict
npx --yes @anthropic-ai/claude-code@2.1.316 plugin validate dist/connected/claude --strict
.venv/bin/python -m worknew_plugins check-backend
```

`check-publication` rapporteert ontbrekende afbeeldingen of videometadata en eindigt met een fout zolang die ontbreken. Het slaat platformchecks niet over. De laatste opdracht leest productie. De overige checks bouwen/valideren lokale bestanden en synthetische fixtures. Geen enkele lokale check bewijst de installatie of werking in een echte ChatGPT-/Claude-host. De buildreport houdt daarom `backendVerified: false`.

De source-manifests declareren de canonieke `.mcp.json`, zodat een installatie uit GitHub meteen een zoekverbinding heeft. Een skills-only-build verwijdert de MCP-declaratie en remote reviewmetadata. Dien voor deze release uitsluitend het **connected** pakket in. Wijzig generated output niet handmatig.

## ChatGPT

Gebruik [OpenAI Plugins](https://platform.openai.com/plugins), **With MCP**, en de verbonden ChatGPT-ZIP. Het pakket bevat de skills, publieke remote server, listingmetadata, vijf positieve en drie negatieve reviewcases en release notes. Voeg de echte video-URL toe zodra de walkthrough is opgenomen. De introductiepagina is geen video.

Selecteer de geverifieerde publisheridentiteit en voltooi de exacte domeinchallenge. Controleer alle skill- en toolscans en de onderbouwing van toolannotaties. Dien pas in na hostacceptatie en correcte policyattestaties; selecteer na goedkeuring afzonderlijk Publish. Deze versie heeft geen custom MCP UI en behoeft daarvoor geen UI-screenshots.

Bronnen: [indienen](https://developers.openai.com/plugins/deploy/submission), [validatieregels](https://developers.openai.com/plugins/deploy/submission-errors).

## Claude

Maak in [Anthropic's developerportal](https://claude.ai/directory/manage) eerst een **MCP connector** voor de publieke server en daarna een **Plugin bundle** voor de GitHub-repositoryroot. Beide horen bij dezelfde organisatie. De server vereist geen gebruikersauthenticatie. De [voorbereide connectorvelden](claude-connector-listing.json) zijn formulierinhoud, geen API-schema.

De directory leest GitHub, niet een lokale ZIP. Publiceer de gereviewde broncommit, valideer die exacte commit in het portal, vul gegevensverwerking in en volg scans en review. De gekoppelde GitHub-gebruiker moet pushrechten hebben en de repository moet publiek zijn wanneer de listing live gaat. Een eigen Claude Code-marketplace staat los van deze publieke directoryroute.

Bronnen: [directoryroute](https://claude.com/docs/directory/publish), [plugin indienen](https://claude.com/docs/plugins/submit), [checklist](https://claude.com/docs/plugins/pre-submission-checklist).

## Reviewmateriaal

De machineleesbare actuele cases staan in `.codex-plugin/plugin.json`. Het [opnamescript](recording-script.md) beschrijft hoe de echte hosttests worden opgenomen. Noteer per host datum, versie, prompt, verwacht resultaat, werkelijk resultaat en bewijs zonder persoonsgegevens. De onderstaande onboarding- en regressiescenario's blijven aanvullend van toepassing.

## Onboardingreview

| Scenario | Verwacht gedrag |
| --- | --- |
| Cv al aanwezig | Hergebruik rollen/vaardigheden; vraag niet opnieuw om hetzelfde cv en verstuur geen identiteit of cv-tekst |
| Cv geweigerd | Accepteer dit direct en vraag naar gewenste rollen |
| Voorkeuren al genoemd | Vat samen en vraag alleen naar relevante ontbrekende informatie; cv is geen vereiste |
| Cv onleesbaar | Leg leesprobleem uit en bied rolvoorkeuren of een vrijwillige samenvatting aan |
| Setup gestart in nieuw/bestaand gesprek | De verpakte get-started-skill wordt geladen; bestaande context wordt hergebruikt |

## Aanvullende zoekregressies

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

Voor N2 moeten backendtests ook ongeldige invoer, onverwachte respons, time-out en pogingen tot `scope`/`personId`-overrides afdekken. Publiceer pas wanneer de openstaande punten aantoonbaar zijn afgehandeld.

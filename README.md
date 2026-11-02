# WorkNew

**Vind jouw volgende opdracht.** Zoek openbare opdrachten voor digital consultants vanuit je gesprek met Claude of ChatGPT. Vertel welke rol je zoekt, vergelijk uren, vergoeding en looptijd, en open de WorkNew-links voor de volledige opdracht.

## Beginnen

Installeer het verbonden WorkNew-pakket en start **get-started**, of vraag meteen: “Zoek via WorkNew drie opdrachten voor een product owner.” Je hebt geen WorkNew-account of API-sleutel nodig. Een account bij je AI-aanbieder met ondersteuning voor plugins en MCP is wel nodig; je workspacebeheerder kan toegang beperken.

Je kunt vrijwillig een cv delen in het gesprek, maar dat hoeft niet. Heb je je voorkeuren al genoemd, dan gebruikt de plugin die. Vraag vervolgens om andere rollen, een vergelijking of meer resultaten.

## Wat de plugin doet

De twee skills, **get-started** en **search-jobs**, helpen je je wensen te formuleren en sturen ondersteunde zoektermen en filters naar de openbare WorkNew-tool **search_jobs** via https://mcp.worknew.co/v1/mcp. De plugin installeert of start geen lokale software en heeft geen automatische installatieacties. De zoekdienst retourneert openbare, open opdrachten en de beschikbare WorkNew-links.

Locatie, reisafstand en thuiswerken zijn geen afzonderlijke zoekfilters. De assistent kan deze voorkeuren vergelijken met de beschikbare resultaatgegevens en noemt ontbrekende informatie. Een afgeschermde opdrachtgever blijft afgeschermd. Controleer de actuele voorwaarden en deadline op de opdrachtpagina.

De plugin verstuurt geen sollicitaties, wijzigt geen gegevens en maakt geen profiel aan. Reageren doe je zelf via WorkNew. Als de zoekverbinding ontbreekt of een storing geeft, meldt de plugin dat; hij verzint geen resultaten.

## Privacy

De skills instrueren je assistent om alleen relevante roltermen, vaardigheden en ondersteunde filters naar WorkNew te sturen. Ze sturen geen cv-bestand, volledige cv-tekst, naam of contactgegevens. Deel zulke persoonsgegevens daarom niet als zoekterm. WorkNew ontvangt de zoekaanvraag en technische gegevens die nodig zijn om die via de dienst te verwerken. Hoe je AI-aanbieder gesprekken en bijlagen bewaart, hangt af van die aanbieder en je instellingen.

Lees de [privacyverklaring](https://worknew.co/legal/privacy) en [servicevoorwaarden](https://worknew.co/legal/terms). De plugin is eigendom van CreateNew Work B.V., handelend onder de naam WorkNew, en wordt aangeboden onder de bijgevoegde [proprietary licentie](LICENSE).

## Hulp

Bekijk de [uitleg en verbindingshandleiding](https://worknew.co/mcp). Controleer bij een fout eerst of WorkNew in je gesprek is ingeschakeld. Lukt het niet, neem contact op met [support@worknew.co](mailto:support@worknew.co). Stuur geen cv of andere persoonsgegevens mee met een technisch foutbericht.

## Status van deze release

Versie **0.4.0** wordt voorbereid voor de publieke directories. De openbare MCP-verbinding is live gecontroleerd; een directorylisting, hostacceptatie en platformgoedkeuring zijn afzonderlijke stappen. Zie [publicatiestatus](docs/publication-readiness.md).

## Ontwikkelen en bouwen

Open `worknewjobs.code-workspace`. De ontwikkeltools gebruiken Python 3.11+; gebruikers van de plugin hoeven geen Python of dependencies te installeren.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m worknew_plugins validate
.venv/bin/python -m worknew_plugins audit
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m worknew_plugins build --skills-only
```

De laatste opdracht bouwt skillpakketten zonder zoekverbinding. De canonieke service-URL is **https://mcp.worknew.co/v1/mcp**. Een gewone build configureert die URL; een build bewijst geen live bereikbaarheid:

```sh
.venv/bin/python -m worknew_plugins build
# Controleer de actuele productieverbinding:
.venv/bin/python -m worknew_plugins check-backend
```

`check-backend` voert discovery en één read-only zoekaanvraag uit. Het toont aantallen, geen cv's of jobpayloads. `build` doet geen netwerkverzoeken en bewijst niet dat een server werkt. Gebruik geen protected REST-URL als MCP-URL. Voor een lokale loopback-HTTP-server voeg je `--development` toe aan beide opdrachten; de tests starten zelf een tijdelijke mockserver.

| Output onder `dist/<modus>/` | Inhoud |
| --- | --- |
| `claude/` en `worknew-jobs-claude-0.4.0.zip` | Claude-manifest, gedeelde skills, bij verbonden builds `.mcp.json` met HTTP-transport |
| `chatgpt/` en `worknew-jobs-chatgpt-0.4.0.zip` | Portable pluginmanifest, onboarding, skills, bij verbonden builds `mcp.json` met Streamable HTTP en `auth.type=none` |
| `backend-contract/` | Publieke tooldefinitie, servicecontract en overdrachtsdocument |
| `build-report.json` | Modus, versie en SHA-256 per ZIP; backendverificatie blijft expliciet false |

Modus is `skills-only`, `connected` of `development`. Builds vervangen alleen hun eigen gegenereerde modusmap. ZIPs bevatten een vaste lijst van bestanden; `.env`, cv's, tests, broncode, developerdependencies en de gitmap gaan niet mee. Alleen expliciet genoemde merkbestanden worden verpakt. Archives zijn reproduceerbaar bij gelijke inputs en toolchain.

## Installeren en beginnen

**Voer na installatie `get-started` uit.** Deel vrijwillig je cv, of vertel welke rollen je zoekt. De skill hergebruikt bestaande gespreksinformatie. Een cv, WorkNew-account of API-sleutel is niet nodig. De plugin uploadt geen cv naar WorkNew en maakt geen profiel aan; voor het gesprek en de bijlage gelden de instellingen van Claude/ChatGPT.

Voor Claude Code kun je een build lokaal laden:

```sh
claude --plugin-dir ./dist/skills-only/claude
```

Start `/worknew-jobs:get-started`. Laad voor een verbonden test de `connected/claude`-map. Gebruik voor Claude-oppervlakken met een custom-plugin-upload de bijbehorende ZIP; beschikbaarheid hangt af van account en productoppervlak.

Gebruik voor ChatGPT de `chatgpt/`-map of ZIP via de ondersteunde lokale/custom pluginroute. Voor openbare distributie van de remote server is **With MCP** in de publicatieportal nodig; een ZIP bouwen registreert geen connector. De setupactie verwijst naar de verpakte `get-started`-skill en wordt door de gebruiker gestart. Er is geen installatiehook. Zie [OpenAI packaging](https://developers.openai.com/plugins/build/plugins) en [Claude-distributie](https://code.claude.com/docs/en/plugins/publish).

## Bronbestanden en volgende stap

| Onderdeel | Doel |
| --- | --- |
| [get-started](skills/get-started/SKILL.md) / [search-jobs](skills/search-jobs/SKILL.md) | Gedeelde onboarding en zoeken, met eerlijk gedrag bij ontbrekende tools |
| [Toolcontract](contracts/search_jobs.json) | Toegestane inputs en publieke output, inclusief MCP-annotaties |
| [Publiek servicecontract](contracts/service.json) | Publieke MCP-URL, authenticatiegrens en veiligheidsvereisten |
| [Backendhandoff](docs/backend-handoff.md) | Normatief publiek backendcontract |
| [Uitrolstatus](docs/deployment-status.md) | Geverifieerde infrastructuur en resterende productiecontroles |
| [Publicatiechecklist](docs/publishing.md) | Branding, links, verificatie en platformreviews |
| [Listingtekst](docs/listing-copy.md) / [assets](assets/README.md) | Nederlandse tekst en nog benodigde merkbestanden |

Pas de twee source-manifests samen aan; `validate` bewaakt identiteit en versie. Wijzig gegenereerde `dist/`-bestanden niet handmatig. Het contract is bron voor backend en checker, geen zoekimplementatie in deze repo. Solliciteren, profielopslag en authenticatie blijven buiten deze versie.

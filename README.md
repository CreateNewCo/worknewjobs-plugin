# WorkNew

**Vind jouw volgende opdracht.** Een Dutch-first plugin voor Claude en ChatGPT, voor digital consultants die opdrachten op [WorkNew](https://www.worknew.co) willen vinden.

**Versie 0.3.0 — pluginzijde gebouwd, productieverbinding in verificatie.** Deze repository bouwt de platformpakketten, bevat gedeelde skills en definieert het openbare zoekcontract. De afzonderlijke MCP-interface is geïmplementeerd in de private WorkNew-backend, met eigen authenticatiebeleid en safeguards. Cloudflare DNS, TLS en de Worker zijn uitgerold. De volledige clienttoegang en directorypublicatie zijn nog niet geverifieerd; zie de [uitrolstatus](docs/deployment-status.md).

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
| `claude/` en `worknew-jobs-claude-0.3.0.zip` | Claude-manifest, gedeelde skills, bij verbonden builds `.mcp.json` met HTTP-transport |
| `chatgpt/` en `worknew-jobs-chatgpt-0.3.0.zip` | Portable pluginmanifest, onboarding, skills, bij verbonden builds `mcp.json` met Streamable HTTP en `auth.type=none` |
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

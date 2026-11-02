# Publieke MCP-integratie

## CURRENT STATE snapshot — 2 november 2026

De plugins zijn geconfigureerd voor **https://mcp.worknew.co/v1/mcp**. DNS, TLS en de Worker zijn uitgerold; de zoekservice is geïmplementeerd. Zie de [uitrolstatus](deployment-status.md) voor geverifieerd gedrag en openstaande clientcontroles. Het [servicecontract](../contracts/service.json) bevat uitsluitend publieke instellingen. Private routes, origins, credentials, configuratienamen en mappings horen niet in deze repository.

## END STATE (normatief)

Claude/ChatGPT → `https://mcp.worknew.co/v1/mcp` → afzonderlijke MCP-interface → gedeelde interne WorkNew-zoeklogica → expliciet toegestane openbare resultaten.

De nieuwe MCP-interface heeft een eigen authenticatie- en beveiligingsgrens. Zij hergebruikt de interne zoeklogica, niet een bestaande frontend-HTTP-route of de authenticatie daarvan. Eventuele interne servicecommunicatie en servicecredentials blijven volledig in de private backendconfiguratie.

### Publiek contract

- Remote Streamable HTTP; alleen de read-only tool `search_jobs`.
- Voor zoeken geen gebruikerslogin, API-sleutel of browserchallenge.
- Alleen openbare, open opdrachten; geen opgeslagen profielinvloed, People-ID, CV-upload of schrijfoperatie.
- Inputs en outputs staan exact in [search_jobs.json](../contracts/search_jobs.json). Defaults worden server-side toegepast. Query maximaal 500 tekens, pagina 1–100 resultaten en niet-negatieve offset.
- Ondersteunde filters: datumperiode, categorie, branche, uren, tariefgroep, duur en exclusiviteit. Locatie/reisafstand/thuiswerken zijn geen aparte filterinputs; de agent mag daarvoor alleen beschikbare resultaatgegevens vergelijken.
- Het publieke antwoord gebruikt neutrale velden zoals `fields.url` en `fields.workMode`. De omzetting van interne velden naar dit contract blijft privaat.
- Geen verborgen opdrachtgevergegevens, interne scores of generieke bronrecords. Een afgeschermde opdrachtgever blijft afgeschermd. Ontbrekende waarden blijven leeg of null volgens het schema.
- MCP-resultaten bevatten dezelfde publieke JSON als `structuredContent` en als één tekstblok. Een backendfout is geen succesvolle lege resultatenlijst.

### Eigen safeguards

De service moet vóór productie onafhankelijke rate limiting, request-/responslimieten, time-outs en concurrencybegrenzing hebben. Pas limieten toe vóór dure retrieval en begrens ook discovery en sessieaanmaak. Een sessie-ID is geen authenticatie of zelfstandig betrouwbare rate-limitidentiteit. Houd rekening met gedeelde uitgaande IP-adressen van AI-platforms. Te veel aanvragen geven HTTP 429 met `Retry-After`; er is geen browserchallenge of automatische onbeperkte retry.

Valideer tools, argumenten, Origins en publieke output. Vertrouw doorgegeven client-IP-headers alleen vanaf een vertrouwde proxy. Bescherm de origin tegen het omzeilen van de edgebeperkingen. Geen willekeurige URLs, private-scope-overrides of CV/contactgegevens in logs. Concrete limieten en originconfiguratie worden in de private backendimplementatie vastgelegd en getest.

Toekomstige login of sollicitaties krijgen expliciete autorisatie en afzonderlijke write-tools; de huidige anonieme zoekinterface verleent die rechten niet.

### Cloudflare en publicatie

Cloudflare kan de hostname proxyen en verzoeken beschermen. DNS configureert de hostname; `/v1/mcp` moet daarnaast door de HTTP-router/edge naar de nieuwe MCP-service worden afgehandeld. De hostname mag geen algemene doorgang naar andere backendroutes worden. Controleer streaming, TLS, Origin-beleid, rate-limitresponses en bereikbaarheid van het bedoelde pad. Gebruik geen DNS-only registratie als bewijs dat Cloudflare HTTP-beperkingen toepast. Zie [Cloudflare proxy status](https://developers.cloudflare.com/dns/proxy-status/) en [routing](https://developers.cloudflare.com/workers/configuration/routing/routes/).

`python -m worknew_plugins build` bouwt beide verbonden pakketten met de vaste publieke URL; `--skills-only` bouwt zonder verbinding. Alleen een expliciete lokale developmentbuild kan een loopbackadres gebruiken. [Het voorbeeld](examples/mcp-config.example.json) toont de Claude-configuratie. Een build voert geen DNS-wijziging, deployment of live check uit.

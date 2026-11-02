# Handoff: publieke WorkNew MCP-service

**END STATE (normatief), contract 2.0.0.** Dit document beschrijft alleen het publieke interfacecontract. De private backendimplementatie en infrastructuurconfiguratie worden afzonderlijk uitgevoerd.

## Afzonderlijke servicegrens

Implementeer remote Streamable HTTP op **https://mcp.worknew.co/v1/mcp**, met uitsluitend `search_jobs`. Maak daarvoor een eigen MCP-route met eigen authenticatiebeleid, validatie en rate limiting. Hergebruik gedeelde interne zoeklogica in plaats van een frontend-API te proxyen. Origins, private routes, credentials en interne veldmappings blijven buiten de publieke pluginrepository.

`service.json` bevat de publieke URL en beleidsvereisten. `search_jobs.json` is de exacte definitie voor `tools/list`: inputSchema, outputSchema en annotaties. De probe vergelijkt schemas exact. Dit nog niet gepubliceerde contract is versie 2.0.0 omdat de resultaatvelden nu providerneutrale namen hebben. De publieke URL-versie blijft `/v1/mcp`.

## Gedrag implementeren

1. Valideer inputs, weiger onbekende properties en vul defaults server-side in. Een JSON Schema-validator vult defaults niet vanzelf in. Trim query en valideer categorie/branche tegen de actuele catalogus.
2. Zoek alleen openbare, open WorkNew-opdrachten. Geen gebruikersprofiel of private-scope-overrides. Behoud de bestaande interne selectie/ranking zonder die naar de plugin te kopiëren.
3. Projecteer uitsluitend `results[].id`, de velden in `fields` en `pagination`. Lever ontbrekende tekst als lege string, logo's als lege array en numerieke/datumwaarden als null. Logo's bevatten hoogstens één toegestaan `{url, filename?}`-object. Geen private opdrachtgevergegevens of bronmetadata.
4. Gebruik `fields.url` voor de canonieke opdrachtlink: HTTPS op exact `worknew.co` of `www.worknew.co`, zonder credentials of afwijkende poort. Een ontbrekende/ongeldige link blijft leeg. Gebruik `fields.workMode` voor de openbare werkwijze. Private veldmappings worden alleen in de backend vastgelegd.
5. Retourneer `isError: false`, `structuredContent` met het publieke resultaat en één tekstblok met dezelfde geserialiseerde JSON. Bij verwerkingsfouten: `isError: true` met veilige tekst. Ongeldige argumenten mogen een MCP invalid-params-error geven. Geen interne foutdetails of credentials.
6. Voeg eigen rate limiting en begrenzingen toe zoals beschreven in de publieke integratiedocumentatie. Pas geen login of browserchallenge toe op anoniem zoeken. Rate limits geven HTTP 429 met `Retry-After`. Stel concrete capaciteit en thresholds vast in de private deploymentconfiguratie.

## Protocol en uitrol

De compatibiliteitsprobe test MCP **2025-11-25**: initialize, initialized, tools/list en tools/call. Ondersteun deze versie naast eventuele nieuwere protocollen met een onderhouden SDK. De probe ondersteunt JSON/direct afgeronde SSE, optionele sessieheaders en geen redirects. Hij test geen resumable SSE, streaming GET, OAuth of de nieuwere lifecycle. Bronnen: [MCP-transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) en [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).

Configureer de Cloudflare-hostname, TLS en route voor `/v1/mcp` afzonderlijk van de pluginbuild. Voorkom dat andere backendroutes via deze hostname toegankelijk worden of dat de origin de bedoelde edgebeperkingen omzeilt. Geen DNS- of backendwijziging is vanuit deze repository uitgevoerd.

Na uitrol, vanuit de pluginrepository:

```sh
.venv/bin/python -m worknew_plugins check-backend
.venv/bin/python -m worknew_plugins build
```

De probe gebruikt standaard de vaste publieke URL, verstuurt één zoekaanvraag en drukt alleen aantallen/status af. Voor lokale tests: `--development --mcp-url` met een loopback-URL. De socket-timeout is 15 seconden, met een SSE-tijdcontrole en een responsgrens van 2 MiB; dit zijn checkerlimieten, geen bewezen productielimieten.

Test backendredactie, gesloten/verborgen opdrachten, verboden overrides, filters, paginering, fouten, rate limiting, Origin-afhandeling en het blokkeren van andere routes. Test vervolgens beide echte hosts. Een geslaagde lokale probe of build is geen bewijs van publieke deployment of volledige gegevensafscherming.

# Uitrolstatus WorkNew MCP

**CURRENT STATE snapshot — 2 november 2026.** Norm: [Publieke MCP-integratie — END STATE](backend-integration.md).

Publieke URL: **https://mcp.worknew.co/v1/mcp**. Gebruikers hebben geen WorkNew-account of API-sleutel nodig.

## Geverifieerd

- De Cloudflare Worker en custom domain zijn aangemaakt; DNS is proxied en HTTPS werkt.
- De twee rate-limitbindings zijn actief. Workers.dev en preview-URLs zijn uitgeschakeld.
- De private verbinding gebruikt een afzonderlijk secret; het staat niet in deze repository of pluginpakketten.
- De backendactivatie is gepusht en de productie-uitrol is live bevestigd.
- De 23 gerichte backendtests voor ingress, MCP en openbaar zoeken slagen met synthetische gegevens.

## Live controles

Uitgevoerd met de expliciete clientheader `User-Agent: WorkNew-MCP-DeploymentCheck/0.3.0`, zonder gebruikersauthenticatie:

- MCP-initialisatie met protocol `2025-11-25`, discovery van uitsluitend `search_jobs` en exacte overeenkomst met het publieke toolcontract.
- Zoeken naar `product designer`: 3 resultaten opgevraagd, 34 matches gemeld op het controlemoment. Deze aantallen veranderen met het aanbod.
- Paginering op offset 0 en 2, met twee resultaten per pagina; outputschema, canonieke links en overeenkomende JSON-/tekstinhoud gevalideerd.
- Een synthetische zoekterm zonder matches geeft een succesvolle lege lijst. Een verzoek om te solliciteren is afgewezen als onbekende tool.
- Private scope-overrides zijn afgewezen. Niet-ondersteunde methodes geven 405; andere paden en querystrings 404; een niet-toegestane Origin 403; gecomprimeerde input 415; een te grote body 413; toegestane preflight 204.
- Directe toegang buiten de voorgeschreven ingress geeft 401.

De rate-limitbindings zijn via de provider teruggelezen en 429-afhandeling is lokaal getest. Er is geen productiebelastingstest of geforceerde backendstoring uitgevoerd. Deze controles vervangen geen echte Claude-/ChatGPT-hosttest.

## Cloudflare-toegang afgerond

Op 2 november 2026 is de standaard Python-client eerst opnieuw met HTTP 403 geweigerd. Na expliciete goedkeuring is via de Cloudflare API MCP een custom rule aangemaakt en teruggelezen voor uitsluitend:

```text
(http.host eq "mcp.worknew.co" and http.request.uri.path eq "/v1/mcp")
```

De actieve regel `worknew_public_mcp_skip_bic` gebruikt **Skip** met uitsluitend `products: ["bic"]` en `logging.enabled: false`. Overige regels, WAF-fases en rate limits worden niet overgeslagen. De Worker-rate-limitbindings en uitgeschakelde workers.dev-/preview-URLs zijn opnieuw via de provider bevestigd. Cloudflare beschrijft deze [gerichte skipactie](https://developers.cloudflare.com/waf/custom-rules/skip/options/).

Daarna slaagde de ongewijzigde checker, zonder aangepaste User-Agent of gebruikersauthenticatie:

```sh
.venv/bin/python -m worknew_plugins check-backend
```

Resultaat: protocol `2025-11-25`, discovery en contractvalidatie van `search_jobs`, 3 resultaten, 38 matches en `hasMore: true`. De aantallen zijn een momentopname. Deze controle bewijst de publieke MCP-verbinding; installatie en onboarding in de echte hosts blijven afzonderlijke acceptatiestappen.

## Resterende platformacceptatie

Controleer vervolgens installatie, onboarding en zoeken in Claude én ChatGPT. Het servicecontract blijft `deploymentStatus: not-verified` totdat de productieacceptatie compleet is. Een buildreport blijft `backendVerified: false`, omdat bouwen zelf geen netwerkcontrole uitvoert.

Branding, privacy-/voorwaardencontrole, platformverificatie, demo en directorypublicatie staan op de [publicatiechecklist](publishing.md). Er is niets bij een directory ingediend.

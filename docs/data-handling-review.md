# Gegevensverwerking voor directoryreview

Concept op basis van de lokale backend- en Worker-broncode, gecontroleerd op 2 november 2026. Dit is onderbouwing voor de indiening, geen vervanging van de privacyverklaring en geen volledige audit van providerlogs of bewaartermijnen.

## Functionele gegevensstroom

De host (ChatGPT of Claude) stuurt zoektermen, toegestane filters en paginering via HTTPS naar de publieke WorkNew MCP-server. Cloudflare verwerkt en stuurt de aanvraag door naar de WorkNew-backend. De backend zoekt in de openbare opdrachtenverzameling en retourneert openbare opdrachtgegevens en links.

De tool heeft geen CV-uploadveld, gebruikersaccount, sollicitatiefunctie of profielopslag. De skills instrueren de host om bij een vrijwillig gedeeld CV alleen relevante beroepskenmerken te gebruiken voor zoektermen. Het CV blijft onder het gegevensbeleid van de host vallen. Vrije zoektekst kan desondanks persoonsgegevens bevatten wanneer de host of gebruiker die daarin opneemt; claim daarom niet dat de dienst technisch uitsluitend anonieme gegevens ontvangt.

## Wat de broncode bevestigt

- De MCP-server verwerkt aanvragen zonder opgeslagen MCP-sessie.
- Netwerkidentiteit wordt voor misbruikbeperking verwerkt. De backend gebruikt een hash van de genormaliseerde netwerkidentiteit voor tijdelijke rate-limitregistraties. Dit is geen bewijs dat netwerkgegevens anoniem zijn.
- Tijdelijke replayregistraties en rate-limitregistraties hebben een vervaltijd. Deze vervaltijden zijn niet gelijk aan de bewaartermijnen van infrastructuur- of beveiligingslogs.
- De specifieke MCP-foutmeldingen loggen categorieën en statuscodes, geen aanvraagtekst. De zoeklaag kan prestatiegegevens loggen, waaronder de lengte van de zoektekst, aantallen, paginering en doorlooptijden.
- De Worker-configuratie schakelt invocation logs en traces uit, maar laat eigen operationele logmeldingen ingeschakeld. Een claim als 'geen logging' is dus onjuist.

De gecontroleerde bronbestanden zijn `cn_worknewMcp.js`, `cn_frontendJobSearch.js`, `cn_redis.js` en de WorkNew MCP Worker-configuratie in de backendrepository. Secrets, interne routes en aanvraaginhoud horen niet in het publicatiepakket of de reviewvideo.

## Nog te bevestigen vóór platformattestaties

1. De gebruiker heeft CreateNew Work B.V. als uitgever bevestigd. Bevestig de rolverdeling voor gegevensverwerking: de publieke privacyverklaring noemt Design-Well B.V.; de servicevoorwaarden noemen CreateNew Work B.V.
2. De daadwerkelijke bewaartermijnen, eventuele logexports, opslaglocaties en toegangsinstellingen bij de betrokken infrastructuurproviders. Lokale broncode bewijst deze accountinstellingen niet.
3. Of de publieke privacyverklaring deze MCP-gegevensstroom voldoende beschrijft. Werk alleen met bevestigde feiten en de gekozen verantwoordelijke rechtspersoon.

Gebruik bij hosttests en video uitsluitend synthetische beroepsprofielen. Claim pas platformacceptatie nadat de betreffende hosttests en portalscans zijn uitgevoerd.

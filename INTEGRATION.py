"""
ZA Support — ISP Outage Monitor: Integration Guide
====================================================

This file documents how the networking integrations are wired together.

FILES ADDED
-----------
1. networking_integrations.py
   - CloudflareRadarProvider
   - IODAProvider
   - RIPEAtlasProvider
   - StatuspageProvider
   - BGPLookingGlassProvider
   - ISPWebhookHandler
   - NetworkingIntegrationManager (orchestrator)

2. router_networking.py
   - FastAPI router mounted at /api/v1/isp
   - Endpoints for webhooks, country health, provider info, per-ISP data

3. detection_engine.py
   - METHOD_WEIGHTS (reliability scoring)
   - CheckResult (individual check)
   - OutageCorrelator (weighted correlation engine)

FILES MODIFIED
--------------
4. app/config.py
   - Added 18 environment variables for all 6 providers + master switch

5. app/schemas.py
   - Added CheckMethod enum (11 methods)
   - Added ISPWebhookPayload model
   - Added ProviderHealthResponse model

6. main.py
   - Added: from router_networking import router as networking_router
   - Added: app.include_router(networking_router)
   - Added "isp_networking" to root endpoint listing

WIRING (main.py)
-----------------
    from router_networking import router as networking_router
    app.include_router(networking_router)

ENVIRONMENT VARIABLES
---------------------
    # Master switch
    NETWORKING_INTEGRATIONS_ENABLED=true

    # Cloudflare Radar
    CLOUDFLARE_RADAR_TOKEN=           # Required for Cloudflare Radar
    CLOUDFLARE_RADAR_ENABLED=true
    CLOUDFLARE_RADAR_CHECK_INTERVAL=300

    # IODA
    IODA_ENABLED=true
    IODA_CHECK_INTERVAL=300
    IODA_COUNTRY_CHECK_ENABLED=true

    # RIPE Atlas
    RIPE_ATLAS_API_KEY=               # Required for creating measurements
    RIPE_ATLAS_ENABLED=true
    RIPE_ATLAS_CHECK_INTERVAL=300

    # Statuspage API
    STATUSPAGE_API_ENABLED=true
    STATUSPAGE_CHECK_INTERVAL=120

    # BGP Looking Glass
    BGP_LOOKING_GLASS_ENABLED=true
    BGP_CHECK_INTERVAL=300

    # Webhooks
    WEBHOOK_ENABLED=true
    WEBHOOK_SIGNATURE_HEADER=X-Webhook-Signature

    # Shared
    PROVIDER_TIMEOUT=20

SA ISP ASN MAPPINGS
-------------------
    afrihost   = AS37611
    rain       = AS327741
    vumatel    = AS328364
    openserve  = AS36874
    rsaweb     = AS37153
    coolideas  = AS328006
    webafrica  = AS37468
    herotel    = AS328210
    vodacom    = AS29975
    mtn        = AS16637
    telkom     = AS5713

RIPE ATLAS SA PROBES
---------------------
    6083  — Johannesburg (generic)
    6354  — Cape Town (generic)
    13498 — Durban (generic)
    14018 — Pretoria (generic)
    30808 — Johannesburg (Vumatel)
    33362 — Cape Town (RSAWEB)
    52148 — Johannesburg (Afrihost)
"""

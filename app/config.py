import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/zasupport")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

API_KEY = os.getenv("API_KEY", "demo_key")
SECRET_KEY = os.getenv("SECRET_KEY", "za-support-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
PORT = int(os.getenv("PORT", "8080"))

# ---------------------------------------------------------------------------
# Networking Integrations — ISP Outage Monitor providers
# ---------------------------------------------------------------------------

# Master switch for all networking integrations
NETWORKING_INTEGRATIONS_ENABLED = os.getenv("NETWORKING_INTEGRATIONS_ENABLED", "true").lower() in ("true", "1", "yes")

# 1. Cloudflare Radar
CLOUDFLARE_RADAR_TOKEN = os.getenv("CLOUDFLARE_RADAR_TOKEN", "")
CLOUDFLARE_RADAR_ENABLED = os.getenv("CLOUDFLARE_RADAR_ENABLED", "true").lower() in ("true", "1", "yes")
CLOUDFLARE_RADAR_CHECK_INTERVAL = int(os.getenv("CLOUDFLARE_RADAR_CHECK_INTERVAL", "300"))

# 2. IODA (CAIDA / Georgia Tech)
IODA_ENABLED = os.getenv("IODA_ENABLED", "true").lower() in ("true", "1", "yes")
IODA_CHECK_INTERVAL = int(os.getenv("IODA_CHECK_INTERVAL", "300"))
IODA_COUNTRY_CHECK_ENABLED = os.getenv("IODA_COUNTRY_CHECK_ENABLED", "true").lower() in ("true", "1", "yes")

# 3. RIPE Atlas
RIPE_ATLAS_API_KEY = os.getenv("RIPE_ATLAS_API_KEY", "")
RIPE_ATLAS_ENABLED = os.getenv("RIPE_ATLAS_ENABLED", "true").lower() in ("true", "1", "yes")
RIPE_ATLAS_CHECK_INTERVAL = int(os.getenv("RIPE_ATLAS_CHECK_INTERVAL", "300"))

# 4. Statuspage API (Atlassian Statuspage JSON)
STATUSPAGE_API_ENABLED = os.getenv("STATUSPAGE_API_ENABLED", "true").lower() in ("true", "1", "yes")
STATUSPAGE_CHECK_INTERVAL = int(os.getenv("STATUSPAGE_CHECK_INTERVAL", "120"))

# 5. BGP Looking Glass (RIPE RIS)
BGP_LOOKING_GLASS_ENABLED = os.getenv("BGP_LOOKING_GLASS_ENABLED", "true").lower() in ("true", "1", "yes")
BGP_CHECK_INTERVAL = int(os.getenv("BGP_CHECK_INTERVAL", "300"))

# 6. Webhooks
WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "true").lower() in ("true", "1", "yes")
WEBHOOK_SIGNATURE_HEADER = os.getenv("WEBHOOK_SIGNATURE_HEADER", "X-Webhook-Signature")

# Shared
PROVIDER_TIMEOUT = int(os.getenv("PROVIDER_TIMEOUT", "20"))

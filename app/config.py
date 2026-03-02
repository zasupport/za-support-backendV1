import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/zasupport")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
PORT = int(os.getenv("PORT", "8080"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# CORS: comma-separated list of allowed origins
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "https://zasupport.com").split(",")
    if o.strip()
]

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# Redis (optional, for ISP monitor cooldowns)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Alert thresholds
CPU_WARNING = float(os.getenv("CPU_WARNING", "80"))
CPU_CRITICAL = float(os.getenv("CPU_CRITICAL", "95"))
MEMORY_WARNING = float(os.getenv("MEMORY_WARNING", "80"))
MEMORY_CRITICAL = float(os.getenv("MEMORY_CRITICAL", "95"))
DISK_WARNING = float(os.getenv("DISK_WARNING", "85"))
DISK_CRITICAL = float(os.getenv("DISK_CRITICAL", "95"))
BATTERY_CRITICAL = float(os.getenv("BATTERY_CRITICAL", "10"))
THREAT_CRITICAL = int(os.getenv("THREAT_CRITICAL", "7"))

# ISP Monitor
ISP_MONITOR_ENABLED = os.getenv("ISP_MONITOR_ENABLED", "false").lower() == "true"
ISP_MONITOR_STATUS_PAGE_CHECK_INTERVAL = int(os.getenv("ISP_MONITOR_STATUS_PAGE_CHECK_INTERVAL", "300"))
ISP_MONITOR_AGENT_HEARTBEAT_TIMEOUT = int(os.getenv("ISP_MONITOR_AGENT_HEARTBEAT_TIMEOUT", "120"))
ISP_MONITOR_OUTAGE_CONFIRMATION_THRESHOLD = int(os.getenv("ISP_MONITOR_OUTAGE_CONFIRMATION_THRESHOLD", "3"))
ISP_MONITOR_ALERT_COOLDOWN_MINS = int(os.getenv("ISP_MONITOR_ALERT_COOLDOWN_MINS", "30"))

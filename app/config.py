import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/zasupport")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

API_KEY = os.getenv("API_KEY", "demo_key")
SECRET_KEY = os.getenv("SECRET_KEY", "za-support-secret-key-change-in-production")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")  # Fernet key — set via env var, not file
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
PORT = int(os.getenv("PORT", "8080"))

# Per-service ports for local dev (ignored on Render — $PORT is injected)
V1_PORT = int(os.getenv("V1_PORT", "8080"))
V3_PORT = int(os.getenv("V3_PORT", "8081"))

# CORS origins — comma-separated list, or "*" for dev
V1_CORS_ORIGINS = os.getenv("V1_CORS_ORIGINS", "*").split(",")
V3_CORS_ORIGINS = os.getenv("V3_CORS_ORIGINS", "*").split(",")

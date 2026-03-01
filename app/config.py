import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/zasupport")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

API_KEY = os.getenv("API_KEY", "demo_key")
SECRET_KEY = os.getenv("SECRET_KEY", "za-support-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
PORT = int(os.getenv("PORT", "8080"))

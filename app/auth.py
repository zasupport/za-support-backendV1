# Backward-compat shim — all auth now lives in app.core.auth
from app.core.auth import *  # noqa: F401,F403
from app.core.auth import (  # noqa: F401
    hash_password, verify_password, create_access_token,
    get_current_user, require_role, verify_api_key,
    pwd_context, oauth2_scheme,
)

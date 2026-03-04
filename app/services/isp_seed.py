# Backward-compat shim — ISP seed now lives in app.modules.isp.seed
from app.modules.isp.seed import *  # noqa: F401,F403
from app.modules.isp.seed import seed_isp_providers  # noqa: F401

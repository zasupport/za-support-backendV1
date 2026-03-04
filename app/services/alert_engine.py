# Backward-compat shim — alert engine now lives in app.modules.alerts.engine
from app.modules.alerts.engine import *  # noqa: F401,F403
from app.modules.alerts.engine import evaluate_health_data, _make_alert  # noqa: F401

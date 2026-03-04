# Backward-compat shim — models now live in their respective modules
# This file re-exports everything so existing imports continue to work.

from app.modules.auth.models import User, UserRole  # noqa: F401
from app.modules.tickets.models import Ticket, TicketStatus, TicketPriority  # noqa: F401
from app.modules.chat.models import ChatSession, ChatMessage, ChatSessionStatus, MessageType  # noqa: F401
from app.modules.devices.models import Device, DeviceType  # noqa: F401
from app.modules.health.models import HealthData  # noqa: F401
from app.modules.network.models import NetworkData  # noqa: F401
from app.modules.alerts.models import Alert, AlertSeverity  # noqa: F401
from app.modules.diagnostics.models import WorkshopDiagnostic  # noqa: F401
from app.modules.isp.models import (  # noqa: F401
    ISPProvider, ISPStatusCheck, AgentConnectivity, ISPOutage,
    ISPStatus, CheckSource, ConnectivityState,
)

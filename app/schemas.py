# Backward-compat shim — schemas now live in their respective modules
# This file re-exports everything so existing imports continue to work.

from app.modules.auth.schemas import (  # noqa: F401
    UserRegister, UserLogin, PasswordChange, RoleUpdate, Token, UserOut,
)
from app.modules.tickets.schemas import TicketCreate, TicketUpdate, TicketOut  # noqa: F401
from app.modules.chat.schemas import (  # noqa: F401
    ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut,
)
from app.modules.devices.schemas import DeviceRegister, DeviceResponse  # noqa: F401
from app.modules.health.schemas import HealthSubmission, HealthOut, HealthResponse  # noqa: F401
from app.modules.network.schemas import NetworkSubmission, NetworkOut  # noqa: F401
from app.modules.alerts.schemas import AlertResponse  # noqa: F401
from app.modules.diagnostics.schemas import (  # noqa: F401
    DeviceHealthSummary, DashboardOverview,
    DiagnosticHardware, DiagnosticMacOS, DiagnosticSecurity, DiagnosticBattery,
    DiagnosticStorage, DiagnosticOCLP, DiagnosticDiagnostics,
    DiagnosticRecommendation, DiagnosticUpload, DiagnosticResponse, DiagnosticSummary,
)
from app.modules.isp.schemas import (  # noqa: F401
    ISPProviderCreate, ISPProviderUpdate, ISPProviderResponse,
    StatusCheckSubmission, StatusCheckResponse,
    AgentHeartbeat, AgentConnectivityResponse,
    ISPOutageCreate, ISPOutageResponse,
    ISPProviderStatus, ISPDashboard,
)

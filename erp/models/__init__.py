"""Public model exports and shared SQLAlchemy handle."""
from __future__ import annotations

# Provide a SQLAlchemy instance early so model modules can import it.
try:
    from ..extensions import db  # type: ignore
except Exception:  # pragma: no cover
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

# Eager exports the tests expect
from .user import User                  # noqa: F401
from .role import Role                  # noqa: F401
from .organization import Organization  # noqa: F401
from .invoice import Invoice            # noqa: F401
from .employee import Employee          # noqa: F401
from .recruitment import Recruitment    # noqa: F401
from .performance_review import PerformanceReview  # noqa: F401
from .user_dashboard import UserDashboard          # noqa: F401
from .order import Order                # noqa: F401
from .hr_lifecycle import (  # noqa: F401
    HROnboarding,
    HROffboarding,
    LeaveRequest,
)
from .crm import (  # noqa: F401
    CRMAccount,
    CRMContact,
    CRMPipelineEvent,
    SupportTicket,
    ClientPortalLink,
)
from .maintenance import (  # noqa: F401
    MaintenanceAsset,
    MaintenanceEscalationEvent,
    MaintenanceEscalationRule,
    MaintenanceEvent,
    MaintenanceSchedule,
    MaintenanceSensorReading,
    MaintenanceWorkOrder,
)
from erp.procurement.models import PurchaseOrder, PurchaseOrderLine
from .audit_log import AuditLog         # noqa: F401
from .core_entities import (            # noqa: F401
    AnalyticsEvent,
    ApprovalRequest,
    BankTransaction,
    ClientRegistration,
    CrmInteraction,
    CrmLead,
    FinanceAccount,
    FinanceEntry,
    InventoryReservation,
    MaintenanceTicket,
    SalesOpportunity,
    SupplyChainShipment,
    UserRoleAssignment,
    RegistrationInvite,
)
from erp.marketing.models import (
    MarketingABVariant,
    MarketingCampaign,
    MarketingConsent,
    MarketingEvent,
    MarketingGeofence,
    MarketingSegment,
    MarketingVisit,
)
from erp.banking.models import (
    BankAccessToken,
    BankAccount,
    BankConnection,
    BankSyncJob,
    BankTwoFactorChallenge,
)
from .finance_gl import (
    GLJournalEntry,
    GLJournalLine,
    FinanceAuditLog,
    BankStatement,
    BankStatementLine,
)
StatementLine = BankStatementLine

# Inventory: try eager, else lazy fallback + back-compat aliases
_BACKCOMPAT_ITEM_NAMES = ("Item", "InventoryItem", "Product", "StockItem")

try:
    from .inventory import Inventory  # noqa: F401
    from erp.inventory.models import (  # noqa: F401
        CycleCount,
        CycleCountLine,
        InventoryLocation,
        InventorySerial,
        Item,
        Lot,
        ReorderRule,
        StockBalance,
        StockLedgerEntry,
        Warehouse,
    )

    Item = Inventory  # noqa: F401
    InventoryItem = Inventory  # noqa: F401
    Product = Inventory  # noqa: F401
    StockItem = Inventory  # noqa: F401
except Exception:  # pragma: no cover
    def __getattr__(name: str):
        if name in ("Inventory",) + _BACKCOMPAT_ITEM_NAMES:
            from . import inventory as _inv
            inv = getattr(_inv, "Inventory", None)
            if inv is None:
                for alias in _BACKCOMPAT_ITEM_NAMES:
                    inv = getattr(_inv, alias, None)
                    if inv is not None:
                        break
            if inv is None:
                raise AttributeError(f"'erp.models' could not resolve {name!r}")
            globals()["Inventory"] = inv
            for alias in _BACKCOMPAT_ITEM_NAMES:
                globals()[alias] = inv
            return globals()[name]
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "db",
    "User", "Role", "Organization", "Invoice",
    "Employee", "Recruitment", "PerformanceReview",
    "HROnboarding", "HROffboarding", "LeaveRequest",
    "CRMAccount", "CRMContact", "CRMPipelineEvent",
    "SupportTicket", "ClientPortalLink",
    "MaintenanceAsset", "MaintenanceSchedule", "MaintenanceWorkOrder", "MaintenanceEvent",
    "MaintenanceEscalationRule", "MaintenanceEscalationEvent", "MaintenanceSensorReading",
    "PurchaseOrder", "PurchaseOrderLine",
    "UserDashboard", "Order",
    "AnalyticsEvent", "ApprovalRequest", "BankTransaction", 
    "ClientRegistration", "CrmInteraction", "CrmLead",
    "FinanceAccount", "FinanceEntry", "InventoryReservation",
    "MaintenanceTicket", "MarketingEvent", "MarketingVisit",
    "MarketingCampaign", "MarketingSegment", "MarketingConsent",
    "MarketingABVariant", "MarketingGeofence",
    "BankAccount", "BankConnection", "BankAccessToken", "BankTwoFactorChallenge", "BankSyncJob",
    "BankStatement", "BankStatementLine", "StatementLine",
    "GLJournalEntry", "GLJournalLine", "FinanceAuditLog",
    "SalesOpportunity", "SupplyChainShipment",
    "UserRoleAssignment", "RegistrationInvite", "AuditLog",
    "Inventory", "Item", "InventoryItem", "Product", "StockItem",
    "Warehouse", "InventoryLocation", "Lot", "InventorySerial", "StockBalance", "StockLedgerEntry",
    "CycleCount", "CycleCountLine", "ReorderRule",
]

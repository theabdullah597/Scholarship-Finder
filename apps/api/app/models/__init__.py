"""Application models package — import all models so Alembic and SQLAlchemy discover them."""

from app.models.ingestion import IngestionRun, IngestionStatus  # noqa: F401
from app.models.opportunity import AuditLog, Opportunity, OpportunityTag, Source, Tag  # noqa: F401
from app.models.student import Application, ApplicationStatus, Note, Notification  # noqa: F401
from app.models.user import RefreshToken, StudentProfile, User  # noqa: F401

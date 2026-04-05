import enum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from apps.base.models import Base


class DdosStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class DdosUrl(Base):
    __tablename__ = 'ddos_urls'

    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    status: Mapped[DdosStatus] = mapped_column(
        Enum(DdosStatus, native_enum=False),
        default=DdosStatus.PENDING,
        nullable=False
    )

    def __str__(self):
        return f"{self.url} ({self.status})"

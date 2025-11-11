"""Class aggregate model"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ClassAggregate(Base, TimestampMixin):
    """
    Class aggregate model storing summary metrics for class cohorts.

    Used for tracking trends over 4-12 week windows and generating
    rollup statistics for class dashboards.

    Attributes:
        class_id: Identifier for the class
        window_start: Start date of the aggregation window
        window_end: End date of the aggregation window
        metric_name: Name of the metric (e.g., "avg_empathy", "growth_collaboration")
        metric_value: Numeric value of the metric
        created_at: Timestamp of record creation
    """

    __tablename__ = "class_aggregates"

    class_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    window_start: Mapped[date] = mapped_column(Date, primary_key=True, nullable=False)
    window_end: Mapped[date] = mapped_column(Date, primary_key=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=4), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ClassAggregate(class={self.class_id}, "
            f"metric={self.metric_name}, "
            f"period={self.window_start} to {self.window_end})>"
        )

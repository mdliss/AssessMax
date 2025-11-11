"""Assessment model"""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Assessment(Base, TimestampMixin):
    """
    Assessment model storing non-academic skill scores for students.

    Skills measured:
    - Empathy: Understanding and sharing feelings of others
    - Adaptability: Adjusting to new conditions
    - Collaboration: Working effectively with others
    - Communication: Expressing ideas clearly
    - Self-regulation: Managing emotions and behavior

    Each skill has a score (0-10) and confidence level (0-1).
    """

    __tablename__ = "assessments"

    assessment_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    assessed_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String, nullable=False)

    # Skill scores (0-10 scale)
    empathy: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=2))
    adaptability: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=2))
    collaboration: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=2))
    communication: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=2))
    self_regulation: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=2))

    # Confidence scores (0-1 scale)
    confidence_empathy: Mapped[Decimal | None] = mapped_column(Numeric(precision=4, scale=3))
    confidence_adaptability: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=4, scale=3)
    )
    confidence_collaboration: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=4, scale=3)
    )
    confidence_communication: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=4, scale=3)
    )
    confidence_self_regulation: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=4, scale=3)
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="assessments")
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Assessment(id={self.assessment_id}, "
            f"student={self.student_id}, date={self.assessed_on})>"
        )

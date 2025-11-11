"""Evidence model"""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Evidence(Base, TimestampMixin):
    """
    Evidence model storing text spans and rationales supporting skill assessments.

    Attributes:
        evidence_id: Primary key UUID
        assessment_id: Foreign key to assessment
        skill: Name of the skill this evidence supports
        span_text: The actual text span extracted as evidence
        span_location: Location reference (e.g., "line 132-168", "page 3")
        rationale: Explanation of why this span supports the skill
        score_contrib: Contribution of this evidence to the overall score
        created_at: Timestamp of record creation
    """

    __tablename__ = "evidence"

    evidence_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.assessment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill: Mapped[str] = mapped_column(String, nullable=False, index=True)
    span_text: Mapped[str] = mapped_column(Text, nullable=False)
    span_location: Mapped[str] = mapped_column(String, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    score_contrib: Mapped[Decimal | None] = mapped_column(Numeric(precision=5, scale=3))

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="evidence")

    def __repr__(self) -> str:
        return (
            f"<Evidence(id={self.evidence_id}, "
            f"skill={self.skill}, location={self.span_location})>"
        )

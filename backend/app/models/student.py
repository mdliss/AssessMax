"""Student model"""

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    """
    Student model representing a middle school student.

    Attributes:
        student_id: Primary key UUID
        class_id: Identifier for the student's class
        name: Student's name (optional for privacy)
        external_ref: Reference to external system ID
        created_at: Timestamp of record creation
    """

    __tablename__ = "students"

    student_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    class_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # Relationships
    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.student_id}, class={self.class_id})>"

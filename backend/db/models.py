from datetime import datetime, timezone

from sqlalchemy import String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

Base = declarative_base()


class Course(Base):
    __tablename__: str = "courses"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint("course_id", name="uq_course_id"),
    )

    # Relationships
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan"
    )
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Course(user_id={self.user_id}, "
            f"course_id={self.course_id}, "
            f"course_name={self.course_name})>"
        )


class Section(Base):
    __tablename__: str = "sections"

    section_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("courses.course_id"), nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="sections")

    def __repr__(self) -> str:
        return (
            f"<Section(section_id={self.section_id}, "
            f"course_id={self.course_id}, title={self.title})>"
        )


class File(Base):
    __tablename__: str = "files"

    path: Mapped[str] = mapped_column(String(500), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    section_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("sections.section_id"), nullable=True
    )
    course_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("courses.course_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="files")

    def __repr__(self) -> str:
        return f"<File(path={self.path}, key={self.key}, section_id={self.section_id})>"

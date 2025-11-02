from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, UniqueConstraint, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

Base = declarative_base()


class User(Base):
    __tablename__: str = "User"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(64), nullable=False)
    ucl_api_token: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_moodle_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    courses: Mapped[list["Course"]] = relationship(
        "Course", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Course(Base):
    __tablename__: str = "Course"

    userId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    courseId: Mapped[str] = mapped_column(
        String(255), primary_key=True, unique=True, nullable=False
    )
    courseName: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint("courseId", name="uq_course_id"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="courses")
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan"
    )
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Course(userId={self.userId}, "
            f"courseId={self.courseId}, "
            f"courseName={self.courseName})>"
        )


class Section(Base):
    __tablename__: str = "Section"

    sectionId: Mapped[str] = mapped_column(
        String(255), primary_key=True, nullable=False
    )
    courseId: Mapped[str] = mapped_column(
        String(255), ForeignKey("Course.courseId"), nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="sections")

    def __repr__(self) -> str:
        return (
            f"<Section(sectionId={self.sectionId}, "
            f"courseId={self.courseId}, title={self.title})>"
        )


class File(Base):
    __tablename__: str = "File"

    path: Mapped[str] = mapped_column(String(500), primary_key=True, nullable=False)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sectionId: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("Section.sectionId"), nullable=True
    )
    courseId: Mapped[str] = mapped_column(
        String(255), ForeignKey("Course.courseId"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="files")

    def __repr__(self) -> str:
        return f"<File(path={self.path}, key={self.key}, sectionId={self.sectionId})>"

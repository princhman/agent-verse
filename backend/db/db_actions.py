from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from db.db import get_session
from db.models import Course, Section, File, User


def add_user(
    email: str,
    password: str,
    ucl_api_token: str | None = None,
    session: Session | None = None,
) -> User | None:
    """
    Add a new user to the database.

    Args:
        email: User email address
        password: User password
        ucl_api_token: Optional UCL API token
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created User object, or None if creation failed
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password=password,
            ucl_api_token=ucl_api_token,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding user: {e}")
        return None
    finally:
        if close_session:
            session.close()


def add_course(
    userId: uuid.UUID,
    courseId: str,
    courseName: str,
    session: Session | None = None,
) -> Course | None:
    """
    Add a new course to the database.

    Args:
        userId: ID of the user who owns this course
        courseId: Unique identifier for the course
        courseName: Name of the course
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created Course object, or None if creation failed

    Raises:
        IntegrityError: If courseId already exists (unique constraint violation)
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        course = Course(
            userId=userId,
            courseId=courseId,
            courseName=courseName,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding course: {e}")
        return None
    finally:
        if close_session:
            session.close()


def add_section(
    sectionId: str,
    courseId: str,
    title: str | None = None,
    content: str | None = None,
    session: Session | None = None,
) -> Section | None:
    """
    Add a new section to the database.

    Args:
        sectionId: Unique identifier for the section
        courseId: ID of the parent course
        title: Optional title of the section
        content: Optional content of the section
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created Section object, or None if creation failed

    Raises:
        IntegrityError: If sectionId already exists or if courseId doesn't exist
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        section = Section(
            sectionId=sectionId,
            courseId=courseId,
            title=title,
            content=content,
            createdAt=datetime.now(timezone.utc),
        )
        session.add(section)
        session.commit()
        session.refresh(section)
        return section
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding section: {e}")
        return None
    finally:
        if close_session:
            session.close()


def add_file(
    path: str,
    key: str,
    courseId: str,
    sectionId: str | None = None,
    session: Session | None = None,
) -> File | None:
    """
    Add a new file to the database.

    Args:
        path: File path (primary key)
        key: Unique key for the file
        courseId: ID of the parent course
        sectionId: Optional ID of the parent section
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created File object, or None if creation failed

    Raises:
        IntegrityError: If path or key already exists, or if courseId/sectionId don't exist
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        file = File(
            path=path,
            key=key,
            courseId=courseId,
            sectionId=sectionId,
            createdAt=datetime.now(timezone.utc),
        )
        session.add(file)
        session.commit()
        session.refresh(file)
        return file
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding file: {e}")
        return None
    finally:
        if close_session:
            session.close()


def add_course_with_sections(
    userId: uuid.UUID,
    courseId: str,
    courseName: str,
    sections_data: list[dict] | None = None,
) -> Course | None:
    """
    Add a new course along with multiple sections in a single transaction.

    Args:
        userId: ID of the user who owns this course
        courseId: Unique identifier for the course
        courseName: Name of the course
        sections_data: Optional list of section dictionaries with keys:
                      'sectionId', 'title' (optional), 'content' (optional)

    Returns:
        The created Course object with all sections, or None if creation failed
    """
    session = get_session()

    try:
        course = Course(
            userId=userId,
            courseId=courseId,
            courseName=courseName,
        )
        session.add(course)

        if sections_data:
            for section_data in sections_data:
                section = Section(
                    sectionId=section_data.get("sectionId"),
                    courseId=courseId,
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    createdAt=datetime.now(timezone.utc),
                )
                session.add(section)

        session.commit()
        session.refresh(course)
        return course
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding course with sections: {e}")
        return None
    finally:
        session.close()


def add_section_with_files(
    sectionId: str,
    courseId: str,
    title: str | None = None,
    content: str | None = None,
    files_data: list[dict] | None = None,
) -> Section | None:
    """
    Add a new section along with multiple files in a single transaction.

    Args:
        sectionId: Unique identifier for the section
        courseId: ID of the parent course
        title: Optional title of the section
        content: Optional content of the section
        files_data: Optional list of file dictionaries with keys:
                   'path', 'key'

    Returns:
        The created Section object with all files, or None if creation failed
    """
    session = get_session()

    try:
        section = Section(
            sectionId=sectionId,
            courseId=courseId,
            title=title,
            content=content,
            createdAt=datetime.now(timezone.utc),
        )
        session.add(section)

        if files_data:
            for file_data in files_data:
                file = File(
                    path=file_data.get("path"),
                    key=file_data.get("key"),
                    courseId=courseId,
                    sectionId=sectionId,
                    createdAt=datetime.now(timezone.utc),
                )
                session.add(file)

        session.commit()
        session.refresh(section)
        return section
    except IntegrityError as e:
        session.rollback()
        print(f"Error adding section with files: {e}")
        return None
    finally:
        session.close()


def add_or_update_course_with_sections(
    userId: uuid.UUID,
    courseId: str,
    courseName: str,
    sections_data: list[dict] | None = None,
) -> Course | None:
    """
    Add a new course with sections, or update if it already exists.
    If course exists, it deletes old sections and replaces them with new ones.

    Args:
        userId: ID of the user who owns this course
        courseId: Unique identifier for the course
        courseName: Name of the course
        sections_data: Optional list of section dictionaries with keys:
                      'sectionId', 'title' (optional), 'content' (optional)

    Returns:
        The created or updated Course object with all sections, or None if operation failed
    """
    session = get_session()

    try:
        # Check if course already exists
        existing_course = (
            session.query(Course).filter(Course.courseId == courseId).first()
        )

        if existing_course:
            # Update existing course
            existing_course.courseName = courseName
            existing_course.userId = userId

            # Delete old sections (cascade will delete associated files)
            session.query(Section).filter(Section.courseId == courseId).delete()

            course = existing_course
            print(f"✓ Updating existing course: {courseId}")
        else:
            # Create new course
            course = Course(
                userId=userId,
                courseId=courseId,
                courseName=courseName,
            )
            session.add(course)
            print(f"✓ Creating new course: {courseId}")

        # Add sections
        if sections_data:
            for section_data in sections_data:
                section = Section(
                    sectionId=section_data.get("sectionId"),
                    courseId=courseId,
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    createdAt=datetime.now(timezone.utc),
                )
                session.add(section)

        session.commit()
        session.refresh(course)
        return course
    except Exception as e:
        session.rollback()
        print(f"Error adding or updating course with sections: {e}")
        return None
    finally:
        session.close()

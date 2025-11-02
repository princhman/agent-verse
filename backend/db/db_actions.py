from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.db import get_session
from db.models import Course, Section, File


def add_course(
    user_id: str,
    course_id: str,
    course_name: str,
    session: Session | None = None,
) -> Course | None:
    """
    Add a new course to the database.

    Args:
        user_id: The ID of the user who owns this course
        course_id: Unique identifier for the course
        course_name: Name of the course
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created Course object, or None if creation failed

    Raises:
        IntegrityError: If course_id already exists (unique constraint violation)
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        course = Course(
            user_id=user_id,
            course_id=course_id,
            course_name=course_name,
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
    section_id: str,
    course_id: str,
    title: str | None = None,
    content: str | None = None,
    session: Session | None = None,
) -> Section | None:
    """
    Add a new section to the database.

    Args:
        section_id: Unique identifier for the section
        course_id: ID of the parent course
        title: Optional title of the section
        content: Optional content of the section
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created Section object, or None if creation failed

    Raises:
        IntegrityError: If section_id already exists or if course_id doesn't exist
    """
    if session is None:
        session = get_session()
        close_session = True
    else:
        close_session = False

    try:
        section = Section(
            section_id=section_id,
            course_id=course_id,
            title=title,
            content=content,
            created_at=datetime.now(timezone.utc),
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
    course_id: str,
    section_id: str | None = None,
    session: Session | None = None,
) -> File | None:
    """
    Add a new file to the database.

    Args:
        path: File path (primary key)
        key: Unique key for the file
        course_id: ID of the parent course
        section_id: Optional ID of the parent section
        session: Optional database session. If not provided, creates a new one.

    Returns:
        The created File object, or None if creation failed

    Raises:
        IntegrityError: If path or key already exists, or if course_id/section_id don't exist
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
            course_id=course_id,
            section_id=section_id,
            created_at=datetime.now(timezone.utc),
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
    user_id: str,
    course_id: str,
    course_name: str,
    sections_data: list[dict] | None = None,
) -> Course | None:
    """
    Add a new course along with multiple sections in a single transaction.

    Args:
        user_id: The ID of the user who owns this course
        course_id: Unique identifier for the course
        course_name: Name of the course
        sections_data: Optional list of section dictionaries with keys:
                      'section_id', 'title' (optional), 'content' (optional)

    Returns:
        The created Course object with all sections, or None if creation failed
    """
    session = get_session()

    try:
        course = Course(
            user_id=user_id,
            course_id=course_id,
            course_name=course_name,
        )
        session.add(course)

        if sections_data:
            for section_data in sections_data:
                section = Section(
                    section_id=section_data.get("section_id"),
                    course_id=course_id,
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    created_at=datetime.now(timezone.utc),
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
    section_id: str,
    course_id: str,
    title: str | None = None,
    content: str | None = None,
    files_data: list[dict] | None = None,
) -> Section | None:
    """
    Add a new section along with multiple files in a single transaction.

    Args:
        section_id: Unique identifier for the section
        course_id: ID of the parent course
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
            section_id=section_id,
            course_id=course_id,
            title=title,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        session.add(section)

        if files_data:
            for file_data in files_data:
                file = File(
                    path=file_data.get("path"),
                    key=file_data.get("key"),
                    course_id=course_id,
                    section_id=section_id,
                    created_at=datetime.now(timezone.utc),
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
    user_id: str,
    course_id: str,
    course_name: str,
    sections_data: list[dict] | None = None,
) -> Course | None:
    """
    Add a new course with sections, or update if it already exists.
    If course exists, it deletes old sections and replaces them with new ones.

    Args:
        user_id: The ID of the user who owns this course
        course_id: Unique identifier for the course
        course_name: Name of the course
        sections_data: Optional list of section dictionaries with keys:
                      'section_id', 'title' (optional), 'content' (optional)

    Returns:
        The created or updated Course object with all sections, or None if operation failed
    """
    session = get_session()

    try:
        # Check if course already exists
        existing_course = (
            session.query(Course).filter(Course.course_id == course_id).first()
        )

        if existing_course:
            # Update existing course
            existing_course.course_name = course_name
            existing_course.user_id = user_id

            # Delete old sections (cascade will delete associated files)
            session.query(Section).filter(Section.course_id == course_id).delete()

            course = existing_course
            print(f"✓ Updating existing course: {course_id}")
        else:
            # Create new course
            course = Course(
                user_id=user_id,
                course_id=course_id,
                course_name=course_name,
            )
            session.add(course)
            print(f"✓ Creating new course: {course_id}")

        # Add sections
        if sections_data:
            for section_data in sections_data:
                section = Section(
                    section_id=section_data.get("section_id"),
                    course_id=course_id,
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    created_at=datetime.now(timezone.utc),
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

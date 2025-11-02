from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import re
from typing import Any
import os
import aiohttp
import hashlib
import uuid

from db.db_actions import add_or_update_course_with_sections, add_file
from db.db import get_session
from s3.s3_client import upload_file_to_s3

MOODLE_URL: str = "https://moodle.ucl.ac.uk"
DOWNLOADS_DIR: str = "/tmp/moodle_downloads"
PAGE_LOAD_TIMEOUT: int = 60000  # 60 seconds for page load


async def fetch_all_available_courses(page: Page) -> list[str]:
    """Fetch all available courses from the Moodle dashboard using Playwright."""
    try:
        await page.goto(f"{MOODLE_URL}/my/courses.php", timeout=PAGE_LOAD_TIMEOUT)
    except Exception as e:
        print(f"  ✗ Failed to navigate to courses page: {e}")
        return []

    # Try networkidle first, fallback to domcontentloaded
    try:
        await page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception as e:
            print(f"  ⚠ Failed to wait for load state: {e}")

    await page.wait_for_timeout(2000)

    all_courses: list[str] = []
    try:
        links = await page.query_selector_all('a[href*="/course/view.php?id="]')

        for link in links[:5]:
            href: str | None = await link.get_attribute("href")
            if href:
                if href.startswith("http"):
                    all_courses.append(href)
                else:
                    all_courses.append(f"{MOODLE_URL}{href}")

        # Remove duplicates
        all_courses = list(set(all_courses))
        print(f"  ✓ Found {len(all_courses)} courses")
    except Exception as e:
        print(f"  ✗ Error extracting courses: {e}")

    return all_courses


async def _download_file_from_url(
    file_url: str,
    filename: str,
    cookies: dict[str, str] | None = None,
) -> str | None:
    """
    Download a file from a URL and save it locally.

    Args:
        file_url: URL of the file to download
        filename: Name to save the file as
        cookies: Optional cookies dict for authentication

    Returns:
        Local file path if successful, None otherwise
    """
    try:
        # Create downloads directory
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)

        # Sanitize filename
        safe_filename = "".join(
            c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")
        )
        file_path = os.path.join(DOWNLOADS_DIR, safe_filename)

        # Download file
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url, cookies=cookies) as response:
                if response.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    return file_path
                else:
                    print(
                        f"      ✗ Failed to download {filename}: HTTP {response.status}"
                    )
                    return None
    except Exception as e:
        print(f"      ✗ Error downloading {filename}: {e}")
        return None


def _build_section_markdown_content(modules: list[dict[str, Any]]) -> str:
    """
    Build markdown content from modules.

    Args:
        modules: List of module dictionaries with name, type, url, and resources

    Returns:
        Markdown formatted string
    """
    if not modules:
        return ""

    markdown_lines: list[str] = []

    for module in modules:
        mod_name = module.get("name", "Unnamed Module")
        mod_type = module.get("type", "unknown")
        mod_url = module.get("url")
        resources = module.get("resources", [])

        # Add module as a heading
        markdown_lines.append(f"### {mod_name}")
        markdown_lines.append(f"**Type:** {mod_type}\n")

        # Add module URL if available
        if mod_url:
            markdown_lines.append(f"[View Module]({mod_url})\n")

        # Add resources/files section
        if resources:
            markdown_lines.append("**Files:**")
            for resource in resources:
                file_name = resource.get("filename", "Unknown File")
                s3_key = resource.get("s3_key", "")
                markdown_lines.append(f"- [{file_name}](s3://{s3_key})")
            markdown_lines.append("")

    return "\n".join(markdown_lines)


def _save_course_to_database(
    course_id: str,
    course_name: str,
    user_id: str,
    sections_data: list[dict[str, Any]],
) -> None:
    """
    Save scraped course data to the database and upload files to S3.

    Args:
        course_id: Unique course identifier
        course_name: Name of the course
        user_id: ID of the user who owns this course
        sections_data: List of section data with modules and files
    """
    session = get_session()

    try:
        # Prepare sections for database
        db_sections: list[dict[str, Any]] = []

        for idx, section in enumerate(sections_data):
            section_name = section.get("name", "")
            modules = section.get("modules", [])

            # Skip sections with no modules
            if not modules:
                continue

            # Build markdown content from modules
            markdown_content = _build_section_markdown_content(modules)

            # Create unique sectionId using section name hash to avoid duplicates
            section_name_hash = hashlib.md5(section_name.encode()).hexdigest()[:8]
            section_id = f"{course_id}_section_{section_name_hash}"

            db_sections.append(
                {
                    "sectionId": section_id,
                    "title": section_name,
                    "content": markdown_content,
                }
            )

        # Add or update course with sections to database
        course = add_or_update_course_with_sections(
            userId=user_id,
            courseId=course_id,
            courseName=course_name,
            sections_data=db_sections,
        )

        if course:
            print(
                f"    ✓ Course '{course_name}' saved to database with {len(db_sections)} sections"
            )

            # Save files for each section and upload to S3
            for idx, section in enumerate(sections_data):
                section_name = section.get("name", "unnamed_section")
                # Recreate the same sectionId using the hash to match what was saved
                section_name_hash = hashlib.md5(section_name.encode()).hexdigest()[:8]
                section_id = f"{course_id}_section_{section_name_hash}"

                for module in section.get("modules", []):
                    for resource in module.get("resources", []):
                        file_name = resource.get("filename", "Unknown File")
                        # Generate a simple key from file name
                        file_key = f"{course_id}_{file_name.replace(' ', '_').replace('.', '_').lower()}"

                        # Build S3 path for the file
                        s3_key = f"courses/{course_id}/{section_name}/{file_name}"

                        # Check if file exists locally (if it was downloaded)
                        local_file_path = resource.get("local_path")
                        uploaded_to_s3 = False

                        if local_file_path and os.path.exists(local_file_path):
                            # Upload file to S3
                            try:
                                success = upload_file_to_s3(
                                    file_path=local_file_path,
                                    s3_key=s3_key,
                                    content_type=resource.get("content_type"),
                                )
                                if success:
                                    uploaded_to_s3 = True
                                else:
                                    print(f"      ✗ Failed to upload {file_name} to S3")
                            except Exception as e:
                                print(f"      ✗ Error uploading {file_name} to S3: {e}")

                        # Use S3 path if uploaded, otherwise use local path
                        file_path = (
                            s3_key
                            if uploaded_to_s3
                            else f"local://{local_file_path}"
                            if local_file_path
                            else s3_key
                        )

                        # Save file metadata to database with S3 path
                        add_file(
                            path=file_path,
                            key=file_key,
                            courseId=course_id,
                            sectionId=section_id,
                            session=session,
                        )

            print(f"    ✓ File metadata and S3 paths saved to database")
        else:
            print(f"    ✗ Failed to save course '{course_name}' to database")

    except Exception as e:
        print(f"    ✗ Error saving course to database: {e}")
    finally:
        session.close()


async def scrape_course_details(
    course_url: str, page: Page, user_id: uuid.UUID | str = "default_user"
) -> dict[str, Any]:
    """Scrape details from a single course page and save to database."""
    try:
        await page.goto(
            course_url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded"
        )
    except Exception as e:
        print(f"  ✗ Failed to navigate to course: {e}")
        return {
            "id": "unknown",
            "name": "Failed to load",
            "url": course_url,
            "sections": [],
            "total_modules": 0,
        }

    # Wait for page to stabilize
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception as e:
        print(f"  ⚠ Load state timeout: {e}")

    await page.wait_for_timeout(1500)

    course_id_match = re.search(r"id=(\d+)", course_url)
    course_id: str = str(course_id_match.group(1)) if course_id_match else "unknown"

    course_name: str = await page.title()

    course_data: dict[str, Any] = {
        "id": course_id,
        "name": course_name,
        "url": course_url,
        "sections": [],
        "total_modules": 0,
    }

    # Use more specific selector to avoid duplicates
    sections = await page.query_selector_all("li.section[data-sectionid]")

    if not sections:
        # Fallback for different Moodle versions
        sections = await page.query_selector_all("div.section")

    seen_sections: set[str] = set()

    for section_element in sections:
        section_name_element = await section_element.query_selector(".sectionname, h3")
        section_name: str = (
            (await section_name_element.inner_text()).strip()
            if section_name_element
            else ""
        )

        # Skip empty section names to avoid duplicates
        if not section_name or section_name.strip() == "":
            continue

        # Skip if we've already processed this section
        if section_name in seen_sections:
            continue

        seen_sections.add(section_name)

        section_data: dict[str, Any] = {
            "name": section_name,
            "modules": [],
        }

        modules = await section_element.query_selector_all(".activity, .modtype_")
        for module_element in modules:
            mod_name_element = await module_element.query_selector(
                ".instancename, span.instancename, a"
            )
            mod_name: str = (
                (await mod_name_element.inner_text()).strip()
                if mod_name_element
                else "Unnamed Module"
            )

            mod_class: str = await module_element.get_attribute("class") or ""
            mod_type_match = re.search(r"modtype_(\w+)", mod_class)
            mod_type: str = mod_type_match.group(1) if mod_type_match else "unknown"

            mod_url_element = await module_element.query_selector("a")
            mod_url: str | None = (
                await mod_url_element.get_attribute("href") if mod_url_element else None
            )

            resources: list[dict[str, Any]] = []
            resource_elements = await module_element.query_selector_all(".fp-filename")
            for resource_element in resource_elements:
                file_name: str = (await resource_element.inner_text()).strip()
                if file_name:
                    # Try to get download link
                    file_link_element = await resource_element.query_selector("..")
                    file_url: str | None = None
                    if file_link_element:
                        file_url = await file_link_element.get_attribute("href")

                    resources.append(
                        {
                            "filename": file_name,
                            "type": "file",
                            "url": file_url,
                            "local_path": None,
                            "content_type": None,
                        }
                    )

            if mod_name:
                section_data["modules"].append(
                    {
                        "name": mod_name,
                        "type": mod_type,
                        "url": mod_url,
                        "resources": resources,
                    }
                )
                course_data["total_modules"] += 1

        if section_data["modules"]:
            course_data["sections"].append(section_data)

    print(f"    ✓ Found {course_data['total_modules']} modules/activities")

    # Download files and prepare for S3 upload
    print(f"  Downloading files...")
    for section in course_data["sections"]:
        for module in section["modules"]:
            for resource in module["resources"]:
                if resource.get("url"):
                    # Download file
                    local_path = await _download_file_from_url(
                        file_url=resource["url"],
                        filename=resource["filename"],
                    )
                    if local_path:
                        resource["local_path"] = local_path
                        print(f"    ✓ Downloaded {resource['filename']}")

    # Save to database and upload to S3
    _save_course_to_database(
        course_id=course_id,
        course_name=course_name,
        user_id=user_id,
        sections_data=course_data["sections"],
    )

    return course_data


async def scrape(
    cookies: list[dict[str, Any]], user_id: uuid.UUID | str = "default_user"
) -> None:
    """Main function to orchestrate the scraping process."""
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch()
        context: BrowserContext = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        )
        page: Page = await context.new_page()

        await context.add_cookies(cookies)
        print("Adding cookies")

        try:
            course_urls: list[str] = await fetch_all_available_courses(page)

            detailed_courses: list[dict[str, Any]] = []
            for idx, url in enumerate(course_urls, 1):
                try:
                    print(
                        f"\n  Scraping course {idx}/{min(2, len(course_urls))}: {url}"
                    )
                    details: dict[str, Any] = await scrape_course_details(
                        url, page, user_id
                    )
                    detailed_courses.append(details)
                except Exception as course_error:
                    print(f"  ✗ Error scraping course {idx}: {course_error}")
                    import traceback

                    traceback.print_exc()
                    continue

        except Exception as e:
            import traceback

            traceback.print_exc()
        finally:
            await browser.close()

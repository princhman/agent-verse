import asyncio
from flask import Flask, jsonify, render_template, request, redirect
from flask_cors import CORS
from playwright.async_api import async_playwright
import json
from scraper import scrape
import webbrowser
from utils.get_room import get_free_rooms
from utils.get_timetable import get_personal_timetable
import requests
from requests import Response
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

start_time = "2025-11-07T00:00:00Z"
end_time = "2025-11-09T00:00:00Z"
client_secret = os.getenv("CLIENT_SECRET")
client_id = os.getenv("CLIENT_ID")
token = ""

app = Flask(__name__)
CORS(app)

# Production flag - set to True when running in production
PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"


@app.route("/login")
def uclapi_login():
    url = "https://uclapi.com/oauth/authorise/?client_id=2816741881293921.8225769007143823&state=1"
    webbrowser.open_new(url)
    return redirect(url)


@app.route("/callback")
def receive_callback():
    # receive parameters
    result = request.args.get("result", "")
    code = request.args.get("code", "")
    state = request.args.get("state", "")

    # e.g. request an auth token from /oauth/tokem
    params: dict = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response: Response = requests.get("https://uclapi.com/oauth/token", params=params)
    token_result: dict = response.json()
    global token
    token = token_result["token"]

    from db.db_actions import add_user
    add_user(email="", password="", ucl_api_token=token, session=None)
    # Generate and return a UUID for the created user
    if user:
        return jsonify({"user_id": str(user.id)})
    else:
        return jsonify({"status": "error", "error": "Failed to create user"}), 500


@app.route("/scrape", methods=["POST"])
def capture_moodle_cookies():
    """Open browser for user to login to UCL Moodle and capture cookies"""
    try:
        # Get user_id from request JSON body
        data = request.get_json()
        user_id_str = data.get("user_id") if data else None

        if not user_id_str:
            return jsonify({"status": "error", "error": "user_id is required"}), 400

        # Validate and convert user_id to UUID
        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            return jsonify(
                {"status": "error", "error": "user_id must be a valid UUID"}
            ), 400

        # Run the async function in an event loop
        cookies = asyncio.run(_capture_cookies_async())

        # Run the scraping in the same event loop
        asyncio.run(scrape(cookies, user_id))

        return jsonify(
            {
                "status": "success",
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


async def _capture_cookies_async():
    """Async function to capture cookies from Moodle login"""
    async with async_playwright() as p:
        # Use headless mode in production, interactive in development
        browser = await p.chromium.launch(headless=PRODUCTION or True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to UCL Moodle
        await page.goto("https://moodle.ucl.ac.uk")

        # Wait for user to login (wait for dashboard to load)
        await page.wait_for_url("**/my/", timeout=300000)  # 5 min timeout

        # Capture cookies and user agent
        cookies = await context.cookies()

        await browser.close()

        return cookies


if __name__ == "__main__":
    # In production, use gunicorn (via Procfile)
    # In development, use Flask's built-in server
    app.run(debug=not PRODUCTION, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

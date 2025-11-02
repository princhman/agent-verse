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

load_dotenv()

start_time = "2025-11-07T00:00:00Z"
end_time = "2025-11-09T00:00:00Z"
client_secret = os.getenv("CLIENT_SECRET")
client_id = os.getenv("CLIENT_ID")
token = ""

app = Flask(__name__)
CORS(app)


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
    # do something with these parameters
    print(result)
    print("code: " + code)

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
    print("token: " + token)
    return redirect("/timetable_results")


@app.route("/room_results")
def room_results():
    data = get_free_rooms(start_time, end_time, token)
    print(data)
    return data


@app.route("/timetable_results")
def timetable_results():
    data = get_personal_timetable(token)
    print(data)
    return data


@app.route("/scrape", methods=["GET"])
def capture_moodle_cookies():
    """Open browser for user to login to UCL Moodle and capture cookies"""
    try:
        # Run the async function in an event loop
        cookies = asyncio.run(_capture_cookies_async())

        # Run the scraping in the same event loop
        asyncio.run(scrape(cookies))

        return jsonify(
            {
                "success": True,
                "message": "Cookies captured successfully and scraped",
                "cookies_count": len(cookies),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


async def _capture_cookies_async():
    """Async function to capture cookies from Moodle login"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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
    app.run(debug=True)

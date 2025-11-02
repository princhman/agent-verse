import requests
from requests import Response
import os
from dotenv import load_dotenv

load_dotenv()

client_secret = os.getenv("CLIENT_SECRET")
client_id = os.getenv("CLIENT_ID")

"""Returns personal timetable filtered by date(OPTIONAL) in YYYY-MM-DD"""
def get_personal_timetable(token, date = ""):

    url: str = "https://uclapi.com/timetable/personal"
    params: dict = {
    "date": date,
    "token": token,
    "client_id": client_id,
    "client_secret": client_secret
    }

    # Make the GET request
    response: Response = requests.get(url, params=params)

    # Check the response is OK and parse the JSON data
    if response.status_code == 200:
        data: dict = response.json()
    
        return data

    else:
        error_message: dict = response.json()
        print(f"Error: {error_message}")
        return None

def main():
    TOKEN = os.getenv("TOKEN")
    data = get_personal_timetable(TOKEN)
    print(data)
    return


if __name__ == '__main__':
    main()

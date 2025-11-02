import requests
from requests import Response
import os
from dotenv import load_dotenv

load_dotenv()

client_secret = os.getenv("CLIENT_SECRET")
client_id = os.getenv("CLIENT_ID")


def get_free_rooms(start_datetime, end_datetime, token):

    # Base URL for geocoding API
    url: str = "https://uclapi.com/roombookings/freerooms"


    params: dict = {
    "start_datetime": start_datetime,
    "end_datetime": end_datetime,
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
    start_time = "2025-11-07T00:00:00Z"
    end_time = "2025-11-09T00:00:00Z"
    data = get_free_rooms(start_time, end_time, TOKEN)
    print(data)
    return


if __name__ == '__main__':
    main()

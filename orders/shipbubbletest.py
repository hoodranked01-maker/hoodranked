import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SHIPBUBBLE_API_KEY")
if not API_KEY:
    raise ValueError("SHIPBUBBLE_API_KEY not found. Check your .env file path.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def create_sender_address():
    url = "https://api.shipbubble.com/v1/shipping/address/validate"
    payload = {
        "name": "HoodRanked Global Ventures",
        "email": "hoodranked2@gmail.com",
        "phone": "+2347070331240",
        "address": "Lead City University, Ibadan, Oyo State, Nigeria",
    }

    response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

    print("Status Code:", response.status_code)
    print("Raw Response:", repr(response.text))

    if not response.text.strip():
        print("Server returned an empty body.")
        return

    data = response.json()
    if response.ok and data.get("status") == "success":
        address_code = data["data"]["address_code"]
        print(f"SHIPBUBBLE_SENDER_ADDRESS_CODE={address_code}")
    else:
        print("API Error:", data)

if __name__ == "__main__":
    create_sender_address()

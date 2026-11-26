import os
import requests
from datetime import date

API_KEY = os.getenv("SHIPBUBBLE_API_KEY")
BASE_URL = "https://api.shipbubble.com/v1"
SENDER_ADDRESS_CODE = int(os.getenv("SHIPBUBBLE_SENDER_ADDRESS_CODE"))
DEFAULT_CATEGORY_ID = int(os.getenv("SHIPBUBBLE_CATEGORY_ID", 98246239))

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

def validate_address(name: str, email: str, phone: str, address: str) -> dict:
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
    }
    r = requests.post(
        f"{BASE_URL}/shipping/address/validate",
        json=payload,
        headers=_headers(),
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise Exception(data.get("message") or "Address validation failed")
    return data["data"]

def fetch_rates(
    receiver_address_code: int,
    package_items: list,
    pickup_date: str = None,
    category_id: int = None,
    package_dimension: dict = None,
) -> dict:
    pickup_date = pickup_date or date.today().isoformat()
    category_id = category_id or DEFAULT_CATEGORY_ID
    package_dimension = package_dimension or {"length": 25, "width": 20, "height": 8}

    payload = {
        "sender_address_code": SENDER_ADDRESS_CODE,
        "reciever_address_code": receiver_address_code,
        "pickup_date": pickup_date,
        "category_id": category_id,
        "package_items": package_items,
        "package_dimension": package_dimension,
        "service_type": "pickup",
    }

    # DEBUG — remove later
    # print("=== SHIPBUBBLE PAYLOAD ===")
    # print(payload)
    # print("==========================")

    r = requests.post(
        f"{BASE_URL}/shipping/fetch_rates",
        json=payload,
        headers=_headers(),
        timeout=20
    )

    # DEBUG — show full response even on error
    # print("=== SHIPBUBBLE RESPONSE ===")
    # print(r.status_code)
    # print(r.text)
    # print("===========================")

    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise Exception(data.get("message") or "Failed to fetch rates")
    return data["data"]

def create_shipment(request_token: str, service_code: str, courier_id: str) -> dict:
    payload = {
        "request_token": request_token,
        "service_code": service_code,
        "courier_id": courier_id,
    }

    # print("=== CREATE SHIPMENT PAYLOAD ===")
    # print(payload)
    # print("===============================")

    r = requests.post(
        f"{BASE_URL}/shipping/labels",
        json=payload,
        headers=_headers(),
        timeout=20
    )

    # print("=== CREATE SHIPMENT RESPONSE ===")
    # print(r.status_code)
    # print(r.text)
    # print("================================")

    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise Exception(data.get("message") or "Failed to create shipment")
    return data["data"]
import requests, hmac, hashlib, time
from config import CLIENT_ID, API_KEY, CHECKSUM_KEY, DOMAIN

PAYOS_URL = "https://api-merchant.payos.vn/v2/payment-requests"

def create_signature(data):
    raw = (
        f"amount={data['amount']}"
        f"&cancelUrl={data['cancelUrl']}"
        f"&description={data['description']}"
        f"&orderCode={data['orderCode']}"
        f"&returnUrl={data['returnUrl']}"
    )
    return hmac.new(
        CHECKSUM_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()

def create_payment(order_code, amount):
    data = {
        "orderCode": int(order_code),
        "amount": int(amount),
        "description": "XacThucDN",
        "returnUrl": f"{DOMAIN}/success",
        "cancelUrl": f"{DOMAIN}/cancel"
    }

    data["signature"] = create_signature(data)

    headers = {
        "x-client-id": CLIENT_ID,
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    res = requests.post(PAYOS_URL, json=data, headers=headers)
    print(res.status_code, res.text)

    return res.json()

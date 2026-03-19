import base64
from io import BytesIO
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def configure_env(db_path: str) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["PAYOS_CLIENT_ID"] = "test-client-id"
    os.environ["PAYOS_API_KEY"] = "test-api-key"
    os.environ["PAYOS_CHECKSUM_KEY"] = "test-checksum-key"
    os.environ["MASTER_REGISTRATION_KEY"] = "test-master-key"
    os.environ["CORS_ORIGINS"] = "*"
    os.environ["PUBLIC_MQTT_BROKER"] = "localhost"
    os.environ["PUBLIC_MQTT_PORT"] = "1883"


DB_FILE = tempfile.NamedTemporaryFile(prefix="vending_backend_full_", suffix=".db", delete=False)
DB_FILE.close()
configure_env(DB_FILE.name)

from app import create_app, db  # noqa: E402
from app.models import DeviceIdentity, DeviceSession, FirmwareUpdate, Order, Transaction, WebAuthnCredential  # noqa: E402


class TestFailure(Exception):
    pass


def create_test_app():
    app = create_app()
    app.config["TESTING"] = True

    @app.route("/api/test/boom")
    def test_boom():
        raise RuntimeError("sensitive internal detail")

    return app


def fail(message: str) -> None:
    raise TestFailure(message)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def expect_status(response, expected_status: int, context: str):
    if response.status_code != expected_status:
        try:
            payload = response.get_json()
        except Exception:
            payload = response.data.decode("utf-8", errors="replace")
        fail(f"{context}: expected HTTP {expected_status}, got {response.status_code}, payload={payload}")
    return response.get_json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def machine_header(machine_key: str) -> dict:
    return {"X-Machine-Key": machine_key}


def step(name: str) -> None:
    print(f"[STEP] {name}")


def main() -> int:
    app = create_test_app()

    try:
        with app.app_context():
            db.drop_all()
            db.create_all()

            client = app.test_client()

            state = {}

            step("Public setup checks")
            payload = expect_status(client.get("/api/users/count"), 200, "GET /api/users/count")
            ensure(payload["count"] == 0, "Initial user count must be 0")

            step("Auth flow")
            payload = expect_status(
                client.post("/api/register", json={"username": "admin", "password": "admin123"}),
                201,
                "POST /api/register",
            )
            state["user_id"] = payload["data"]["user_id"]

            expect_status(
                client.post("/api/register", json={"username": "admin2", "password": "admin123"}),
                403,
                "POST /api/register second user",
            )
            expect_status(
                client.post("/api/login", json={"username": "admin", "password": "wrong"}),
                401,
                "POST /api/login invalid credentials",
            )
            payload = expect_status(
                client.post("/api/login", json={"username": "admin", "password": "admin123"}),
                200,
                "POST /api/login valid",
            )
            token = payload["data"]["access_token"]

            expect_status(client.get("/api/users/me", headers=auth_header(token)), 200, "GET /api/users/me")
            payload = expect_status(client.get("/api/users", headers=auth_header(token)), 200, "GET /api/users")
            ensure(len(payload["data"]) == 1, "Expected exactly one user after registration")

            payload = expect_status(
                client.put(
                    f"/api/users/{state['user_id']}",
                    headers=auth_header(token),
                    json={"username": "admin2", "password": "newpass123", "is_active": True},
                ),
                200,
                "PUT /api/users/<id>",
            )
            ensure(payload["data"]["username"] == "admin2", "Username update failed")
            expect_status(
                client.post("/api/login", json={"username": "admin", "password": "admin123"}),
                401,
                "POST /api/login old username should fail",
            )
            payload = expect_status(
                client.post("/api/login", json={"username": "admin2", "password": "newpass123"}),
                200,
                "POST /api/login updated credentials",
            )
            token = payload["data"]["access_token"]

            step("Machine CRUD")
            machine_1 = {
                "name": "Machine 1",
                "location": "Floor 1",
                "status": "active",
                "secret_key": "machine-key-1",
                "mqtt_command_topic": "vending/m1/cmd",
                "mqtt_status_topic": "vending/m1/status",
                "mqtt_broadcast_status_topic": "vending/status",
                "ui_layout": {"theme": "factory"},
                "device_profile": {"cash_enabled": True},
                "config_notes": "Primary machine",
            }
            payload = expect_status(
                client.post("/api/machines", headers=auth_header(token), json=machine_1),
                201,
                "POST /api/machines machine1",
            )
            state["machine_1_id"] = payload["data"]["machine_id"]

            machine_2 = {
                "name": "Machine 2",
                "location": "Floor 2",
                "status": "active",
                "secret_key": "machine-key-2",
                "mqtt_command_topic": "vending/m2/cmd",
                "mqtt_status_topic": "vending/m2/status",
                "mqtt_broadcast_status_topic": "vending/status",
                "ui_layout": {"theme": "forest"},
                "device_profile": {"cash_enabled": False},
                "config_notes": "Secondary machine",
            }
            payload = expect_status(
                client.post("/api/machines", headers=auth_header(token), json=machine_2),
                201,
                "POST /api/machines machine2",
            )
            state["machine_2_id"] = payload["data"]["machine_id"]

            payload = expect_status(client.get("/api/machines", headers=auth_header(token)), 200, "GET /api/machines")
            ensure(len(payload["data"]) == 2, "Expected two machines")

            machine_1["ui_layout"] = {"theme": "factory", "title": "Machine One"}
            machine_1["device_profile"] = {"cash_enabled": True, "device_mode": "standard"}
            payload = expect_status(
                client.put(
                    f"/api/machines/{state['machine_1_id']}",
                    headers=auth_header(token),
                    json=machine_1,
                ),
                200,
                "PUT /api/machines/<id>",
            )
            ensure(payload["data"]["ui_layout"]["title"] == "Machine One", "Machine update did not persist ui_layout")

            expect_status(
                client.get(
                    f"/api/machines/{state['machine_1_id']}",
                    headers=machine_header(machine_1["secret_key"]),
                ),
                200,
                "GET /api/machines/<id> with machine key",
            )

            step("Product CRUD")
            product_payload = {
                "product_name": "Water Bottle",
                "price": 15000,
                "image": "/static/uploads/water.png",
                "active": True,
            }
            payload = expect_status(
                client.post("/api/products", headers=auth_header(token), json=product_payload),
                201,
                "POST /api/products",
            )
            state["product_id"] = payload["data"]["product_id"]
            payload = expect_status(
                client.put(
                    f"/api/products/{state['product_id']}",
                    headers=auth_header(token),
                    json={
                        "product_name": "Water Bottle Premium",
                        "price": 15000,
                        "image": "/static/uploads/water.png",
                        "active": True,
                    },
                ),
                200,
                "PUT /api/products/<id>",
            )
            ensure(payload["data"]["product_name"] == "Water Bottle Premium", "Product update failed")
            expect_status(
                client.get("/api/products", headers=machine_header(machine_1["secret_key"])),
                200,
                "GET /api/products with machine key",
            )

            step("Upload image")
            payload = expect_status(
                client.post(
                    "/api/upload",
                    headers=auth_header(token),
                    data={"file": (BytesIO(b"fake-png-content"), "product.png")},
                    content_type="multipart/form-data",
                ),
                200,
                "POST /api/upload valid image",
            )
            ensure(payload["data"]["url"].startswith("/static/uploads/"), "Upload did not return static upload URL")
            expect_status(
                client.post(
                    "/api/upload",
                    headers=auth_header(token),
                    data={"file": (BytesIO(b"not-allowed"), "product.txt")},
                    content_type="multipart/form-data",
                ),
                400,
                "POST /api/upload invalid extension",
            )

            step("Slot CRUD")
            slot_1_payload = {
                "machine_id": state["machine_1_id"],
                "slot_code": "A1",
                "product_id": state["product_id"],
                "stock": 5,
                "capacity": 10,
            }
            payload = expect_status(
                client.post("/api/slots", headers=auth_header(token), json=slot_1_payload),
                201,
                "POST /api/slots machine1 A1",
            )
            state["slot_1_id"] = payload["data"]["slot_id"]
            expect_status(
                client.post("/api/slots", headers=auth_header(token), json=slot_1_payload),
                400,
                "POST /api/slots duplicate slot",
            )
            payload = expect_status(
                client.post(
                    "/api/slots",
                    headers=auth_header(token),
                    json={
                        "machine_id": state["machine_2_id"],
                        "slot_code": "B1",
                        "product_id": state["product_id"],
                        "stock": 3,
                        "capacity": 10,
                    },
                ),
                201,
                "POST /api/slots machine2 B1",
            )
            state["slot_2_id"] = payload["data"]["slot_id"]
            expect_status(
                client.get(f"/api/slots?machine_id={state['machine_1_id']}", headers=auth_header(token)),
                200,
                "GET /api/slots filtered",
            )

            step("IoT machine setup")
            expect_status(
                client.post("/api/iot/ping", headers=machine_header(machine_1["secret_key"]), json={"status": "online"}),
                200,
                "POST /api/iot/ping",
            )
            expect_status(
                client.post(
                    "/api/iot/frontend-heartbeat",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"session_id": "session-1"},
                ),
                200,
                "POST /api/iot/frontend-heartbeat session-1",
            )
            expect_status(
                client.post(
                    "/api/iot/frontend-heartbeat",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"session_id": "session-2"},
                ),
                403,
                "POST /api/iot/frontend-heartbeat conflicting session",
            )
            payload = expect_status(
                client.post(
                    "/api/iot/register-device",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"mac_address": "AA:BB:CC:DD:EE:01", "fingerprint": "fp-1"},
                ),
                201,
                "POST /api/iot/register-device machine key",
            )
            ensure(payload["data"]["config"]["machine_id"] == str(state["machine_1_id"]), "register-device returned wrong machine")

            payload = expect_status(
                client.post(
                    "/api/iot/register-device",
                    headers=machine_header(os.environ["MASTER_REGISTRATION_KEY"]),
                    json={
                        "machine_id": state["machine_1_id"],
                        "mac_address": "AA:BB:CC:DD:EE:02",
                        "fingerprint": "fp-master",
                    },
                ),
                201,
                "POST /api/iot/register-device with master key",
            )
            ensure(payload["data"]["machine_id"] == state["machine_1_id"], "master registration returned wrong machine")

            payload = expect_status(
                client.post(
                    "/api/iot/heartbeat",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"uptime": 3600, "free_memory": 50000, "wifi_rssi": -60, "wifi_ssid": "TestWiFi"},
                ),
                200,
                "POST /api/iot/heartbeat",
            )
            state["device_session_id"] = payload["data"]["session_id"]

            expect_status(
                client.post(
                    "/api/iot/logs",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"level": "warning", "message": "sensor drift", "data": {"sensor": "temp"}},
                ),
                201,
                "POST /api/iot/logs",
            )
            expect_status(
                client.post(
                    "/api/iot/report-log",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"level": "info", "message": "device boot"},
                ),
                200,
                "POST /api/iot/report-log",
            )

            step("Device admin APIs")
            payload = expect_status(client.get("/api/devices/identity", headers=auth_header(token)), 200, "GET /api/devices/identity")
            ensure(len(payload["data"]) >= 1, "Expected at least one device identity")
            payload = expect_status(client.get("/api/devices/sessions", headers=auth_header(token)), 200, "GET /api/devices/sessions")
            ensure(len(payload["data"]) >= 1, "Expected at least one device session")
            expect_status(
                client.post(
                    "/api/devices/identity",
                    headers=auth_header(token),
                    json={
                        "machine_id": state["machine_2_id"],
                        "device_public_key": "manual-key",
                        "cert_fingerprint": "manual-fingerprint",
                        "secure_element_id": "se-1",
                        "mac_address": "AA:BB:CC:DD:EE:22",
                        "status": "active",
                    },
                ),
                201,
                "POST /api/devices/identity",
            )
            payload = expect_status(
                client.post(
                    "/api/devices/sessions",
                    headers=auth_header(token),
                    json={
                        "machine_id": state["machine_2_id"],
                        "token_hash": "manual-session-token",
                        "expires_at": "2030-01-01T00:00:00",
                        "ip_address": "127.0.0.1",
                    },
                ),
                201,
                "POST /api/devices/sessions",
            )
            state["manual_session_id"] = payload["data"]["session_id"]
            expect_status(
                client.put(
                    f"/api/devices/sessions/{state['manual_session_id']}/revoke",
                    headers=auth_header(token),
                ),
                200,
                "PUT /api/devices/sessions/<id>/revoke",
            )
            with patch("app.routes.device.send_machine_command", return_value=True):
                expect_status(
                    client.post(
                        f"/api/devices/{state['machine_1_id']}/action",
                        headers=auth_header(token),
                        json={"action": "TEST_MOTOR", "data": "A1"},
                    ),
                    200,
                    "POST /api/devices/<id>/action",
                )
            expect_status(client.get("/api/devices/logs", headers=auth_header(token)), 200, "GET /api/devices/logs")

            step("WebAuthn flow")
            payload = expect_status(client.get("/api/webauthn/status", headers=auth_header(token)), 200, "GET /api/webauthn/status initial")
            ensure(payload["data"]["has_passkey"] is False, "User should not have passkey initially")

            fake_registration_options = type("FakeRegistrationOptions", (), {"challenge": b"register-challenge"})()
            fake_registration_verification = type(
                "FakeRegistrationVerification",
                (),
                {
                    "credential_id": b"credential-123",
                    "credential_public_key": b"public-key-123",
                    "sign_count": 1,
                    "aaguid": "fake-aaguid",
                },
            )()

            with patch("app.routes.webauthn.generate_registration_options", return_value=fake_registration_options), patch(
                "app.routes.webauthn.options_to_json",
                return_value={"challenge": "register-options"},
            ):
                payload = expect_status(
                    client.post("/api/webauthn/register/begin", headers=auth_header(token)),
                    200,
                    "POST /api/webauthn/register/begin",
                )
                ensure(payload["data"]["challenge"] == "register-options", "Unexpected WebAuthn register begin payload")

            with patch(
                "app.routes.webauthn.verify_registration_response",
                return_value=fake_registration_verification,
            ):
                payload = expect_status(
                    client.post(
                        "/api/webauthn/register/complete",
                        headers=auth_header(token),
                        json={
                            "id": "credential-id",
                            "rawId": base64.urlsafe_b64encode(b"credential-123").decode().rstrip("="),
                            "response": {"clientDataJSON": "x", "attestationObject": "y", "transports": ["internal"]},
                            "type": "public-key",
                            "device_name": "Test Passkey",
                        },
                    ),
                    200,
                    "POST /api/webauthn/register/complete",
                )
                ensure(payload["success"] is True, "WebAuthn register complete failed")

            payload = expect_status(client.get("/api/webauthn/status", headers=auth_header(token)), 200, "GET /api/webauthn/status after register")
            ensure(payload["data"]["has_passkey"] is True, "Passkey should exist after registration")
            ensure(payload["data"]["device_name"] == "Test Passkey", "Unexpected passkey device name")

            expect_status(
                client.post("/api/webauthn/register/begin", headers=auth_header(token)),
                400,
                "POST /api/webauthn/register/begin duplicate",
            )

            fake_authentication_options = type("FakeAuthenticationOptions", (), {"challenge": b"login-challenge"})()
            with patch("app.routes.webauthn.generate_authentication_options", return_value=fake_authentication_options), patch(
                "app.routes.webauthn.options_to_json",
                return_value={"challenge": "login-options"},
            ):
                payload = expect_status(
                    client.post("/api/webauthn/login/begin", json={"username": "admin2"}),
                    200,
                    "POST /api/webauthn/login/begin",
                )
                state["webauthn_session_key"] = payload["session_key"]

            fake_authentication_verification = type("FakeAuthenticationVerification", (), {"new_sign_count": 2})()
            with patch(
                "app.routes.webauthn.verify_authentication_response",
                return_value=fake_authentication_verification,
            ):
                payload = expect_status(
                    client.post(
                        "/api/webauthn/login/complete",
                        json={
                            "session_key": state["webauthn_session_key"],
                            "rawId": base64.urlsafe_b64encode(b"credential-123").decode().rstrip("="),
                            "id": "credential-id",
                            "response": {
                                "clientDataJSON": "x",
                                "authenticatorData": "y",
                                "signature": "z",
                            },
                            "type": "public-key",
                        },
                    ),
                    200,
                    "POST /api/webauthn/login/complete",
                )
                ensure(payload["data"]["username"] == "admin2", "WebAuthn login returned wrong user")

            expect_status(
                client.delete("/api/webauthn/remove", headers=auth_header(token), json={"password": "wrong"}),
                401,
                "DELETE /api/webauthn/remove wrong password",
            )
            expect_status(
                client.delete("/api/webauthn/remove", headers=auth_header(token), json={"password": "newpass123"}),
                200,
                "DELETE /api/webauthn/remove success",
            )
            payload = expect_status(client.get("/api/webauthn/status", headers=auth_header(token)), 200, "GET /api/webauthn/status after remove")
            ensure(payload["data"]["has_passkey"] is False, "Passkey should be removed")

            step("Pending order and payment creation")
            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={
                        "product_id": state["product_id"],
                        "slot_id": state["slot_1_id"],
                        "quantity": 2,
                        "price_snapshot": 1,
                    },
                ),
                201,
                "POST /api/orders/pending",
            )
            state["pending_order_id"] = payload["data"]["order_id"]
            ensure(payload["data"]["price_snapshot"] == 30000.0, "Pending order price was not calculated server-side")

            expect_status(
                client.post(
                    "/api/payment/create",
                    headers=machine_header(machine_1["secret_key"]),
                    json={
                        "order_code": state["pending_order_id"],
                        "amount": 12000,
                        "description": "invalid amount",
                        "items": [{"name": "Water", "quantity": 2, "price": 6000}],
                    },
                ),
                400,
                "POST /api/payment/create mismatched amount",
            )

            with patch("app.routes.payment.create_payment_link") as mocked_create_payment_link:
                mocked_create_payment_link.return_value = {
                    "success": True,
                    "checkout_url": "https://checkout.test/abc",
                    "qr_code": "qr-abc",
                    "payment_code": state["pending_order_id"] * 10000 + 1,
                }
                payload = expect_status(
                    client.post(
                        "/api/payment/create",
                        headers=machine_header(machine_1["secret_key"]),
                        json={
                            "order_code": state["pending_order_id"],
                            "amount": 30000,
                            "description": "valid payment",
                            "items": [{"name": "Water", "quantity": 2, "price": 15000}],
                        },
                    ),
                    201,
                    "POST /api/payment/create valid",
                )
                ensure(mocked_create_payment_link.call_args.kwargs["amount"] == 30000, "Payment creation used wrong amount")
                state["pending_payment_code"] = payload["data"]["payment_code"]
            expect_status(
                client.post(
                    f"/api/orders/{state['pending_order_id']}/cancel",
                    headers=machine_header(machine_1["secret_key"]),
                ),
                200,
                "POST /api/orders/<id>/cancel cleanup",
            )

            step("Payment cancel flow")
            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"product_id": state["product_id"], "slot_id": state["slot_1_id"], "quantity": 1},
                ),
                201,
                "POST /api/orders/pending for cancel flow",
            )
            cancel_order_id = payload["data"]["order_id"]
            with patch("app.routes.payment.cancel_payment", return_value={"success": True, "message": "cancelled"}):
                expect_status(
                    client.post(
                        f"/api/payment/cancel/{cancel_order_id}",
                        headers=machine_header(machine_1["secret_key"]),
                    ),
                    200,
                    "POST /api/payment/cancel/<order_code>",
                )
            cancelled_order = db.session.get(Order, cancel_order_id)
            ensure(cancelled_order.status_payment == "cancelled", "Cancel payment did not update order")

            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"product_id": state["product_id"], "slot_id": state["slot_1_id"], "quantity": 1},
                ),
                201,
                "POST /api/orders/pending for cancel page",
            )
            cancel_page_order_id = payload["data"]["order_id"]
            payload = expect_status(
                client.get(f"/api/payment/cancel?orderCode={cancel_page_order_id}"),
                200,
                "GET /api/payment/cancel",
            )
            ensure(payload["order_id"] == cancel_page_order_id, "Cancel page returned wrong order id")

            step("Webhook and dispense flow")
            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"product_id": state["product_id"], "slot_id": state["slot_1_id"], "quantity": 1},
                ),
                201,
                "POST /api/orders/pending for webhook flow",
            )
            state["webhook_order_id"] = payload["data"]["order_id"]
            webhook_payment_code = state["webhook_order_id"] * 10000 + 7

            webhook_payload = {
                "code": "00",
                "desc": "success",
                "success": True,
                "data": {
                    "orderCode": webhook_payment_code,
                    "amount": 15000,
                    "description": "Webhook payment",
                    "reference": "bank-ref-1",
                },
                "signature": "valid-signature",
            }

            with patch("app.routes.payment.verify_webhook_signature", return_value=True), patch(
                "app.routes.payment.send_dispense_command",
                return_value=True,
            ), patch("app.routes.payment.emit_payment_success", return_value=None):
                expect_status(client.post("/api/payment/webhook", json=webhook_payload), 200, "POST /api/payment/webhook")
                expect_status(
                    client.post("/api/payment/webhook", json=webhook_payload),
                    200,
                    "POST /api/payment/webhook duplicate",
                )

            webhook_order = db.session.get(Order, state["webhook_order_id"])
            ensure(webhook_order.status_payment == "completed", "Webhook did not complete order")

            payload = expect_status(
                client.get(
                    f"/api/iot/check-payment/{state['webhook_order_id']}",
                    headers=machine_header(machine_1["secret_key"]),
                ),
                200,
                "GET /api/iot/check-payment owner",
            )
            ensure(payload["data"]["paid"] is True, "Owner machine did not see paid order")

            expect_status(
                client.get(
                    f"/api/iot/check-payment/{state['webhook_order_id']}",
                    headers=machine_header(machine_2["secret_key"]),
                ),
                403,
                "GET /api/iot/check-payment foreign machine",
            )

            payload = expect_status(
                client.get("/api/iot/pending-orders", headers=machine_header(machine_1["secret_key"])),
                200,
                "GET /api/iot/pending-orders",
            )
            pending_ids = {item["order_id"] for item in payload["data"]}
            ensure(state["webhook_order_id"] in pending_ids, "Paid pending-dispense order missing from pending-orders")

            expect_status(
                client.post(
                    "/api/iot/dispense-complete",
                    headers=machine_header(machine_2["secret_key"]),
                    json={"order_id": state["webhook_order_id"], "success": True},
                ),
                403,
                "POST /api/iot/dispense-complete foreign machine",
            )
            expect_status(
                client.post(
                    "/api/iot/dispense-complete",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"order_id": state["webhook_order_id"], "success": True},
                ),
                200,
                "POST /api/iot/dispense-complete owner",
            )
            webhook_order = db.session.get(Order, state["webhook_order_id"])
            ensure(webhook_order.status_slots == "dispensed", "Dispense completion did not update status_slots")

            step("Payment status and sync flows")
            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"product_id": state["product_id"], "slot_id": state["slot_1_id"], "quantity": 1},
                ),
                201,
                "POST /api/orders/pending for payment status",
            )
            status_order_id = payload["data"]["order_id"]
            with patch(
                "app.routes.payment.get_payment_status",
                return_value={
                    "success": True,
                    "order_code": status_order_id,
                    "status": "PAID",
                    "amount": 15000,
                    "amount_paid": 15000,
                    "amount_remaining": 0,
                    "transactions": [{"reference": "poll-ref", "status": "SUCCESS"}],
                },
            ), patch("app.routes.payment.send_dispense_command", return_value=True), patch(
                "app.routes.payment.emit_payment_success",
                return_value=None,
            ):
                expect_status(
                    client.get(
                        f"/api/payment/status/{status_order_id}",
                        headers=machine_header(machine_1["secret_key"]),
                    ),
                    200,
                    "GET /api/payment/status/<order_code>",
                )
            ensure(db.session.get(Order, status_order_id).status_payment == "completed", "Payment status poll did not settle order")

            payload = expect_status(
                client.post(
                    "/api/orders/pending",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"product_id": state["product_id"], "slot_id": state["slot_1_id"], "quantity": 1},
                ),
                201,
                "POST /api/orders/pending for payment sync",
            )
            sync_order_id = payload["data"]["order_id"]
            with patch(
                "app.routes.payment.get_payment_status",
                return_value={
                    "success": True,
                    "order_code": sync_order_id,
                    "status": "SUCCESS",
                    "amount": 15000,
                    "amount_paid": 15000,
                    "amount_remaining": 0,
                    "transactions": [{"reference": "sync-ref", "status": "SUCCESS"}],
                },
            ), patch("app.routes.payment.send_dispense_command", return_value=True), patch(
                "app.routes.payment.emit_payment_success",
                return_value=None,
            ):
                expect_status(
                    client.post(
                        f"/api/payment/sync/{sync_order_id}",
                        headers=machine_header(machine_1["secret_key"]),
                    ),
                    200,
                    "POST /api/payment/sync/<order_code>",
                )
            ensure(db.session.get(Order, sync_order_id).status_payment == "completed", "Manual payment sync did not settle order")

            step("Cash payment flow")
            payload = expect_status(
                client.post(
                    "/api/iot/create-order",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"slot_code": "A1", "quantity": 1},
                ),
                201,
                "POST /api/iot/create-order",
            )
            state["cash_order_id"] = payload["data"]["order_id"]
            expect_status(
                client.get(
                    f"/api/iot/cash-status/{state['cash_order_id']}",
                    headers=machine_header(machine_1["secret_key"]),
                ),
                200,
                "GET /api/iot/cash-status before insert",
            )
            payload = expect_status(
                client.post(
                    "/api/iot/cash-insert",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"order_id": state["cash_order_id"], "denomination": 10000},
                ),
                200,
                "POST /api/iot/cash-insert partial",
            )
            ensure(payload["paid"] is False, "First cash insert should not complete payment")
            payload = expect_status(
                client.post(
                    "/api/iot/cash-insert",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"order_id": state["cash_order_id"], "denomination": 10000},
                ),
                200,
                "POST /api/iot/cash-insert complete",
            )
            ensure(payload["paid"] is True, "Second cash insert should complete payment")
            payload = expect_status(
                client.get(
                    f"/api/iot/cash-status/{state['cash_order_id']}",
                    headers=machine_header(machine_1["secret_key"]),
                ),
                200,
                "GET /api/iot/cash-status after insert",
            )
            ensure(payload["data"]["status_payment"] == "completed", "Cash status did not reflect completed payment")

            step("Legacy order and transaction routes")
            payload = expect_status(
                client.post(
                    "/api/orders",
                    json={
                        "product_id": state["product_id"],
                        "price_snapshot": 15000,
                        "slot_id": state["slot_2_id"],
                        "status_payment": "completed",
                        "status_slots": "completed",
                    },
                ),
                201,
                "POST /api/orders legacy",
            )
            legacy_order_id = payload["data"]["order_id"]
            expect_status(client.get(f"/api/orders/{legacy_order_id}", headers=auth_header(token)), 200, "GET /api/orders/<id>")
            payload = expect_status(
                client.post(
                    "/api/transactions",
                    json={
                        "order_id": legacy_order_id,
                        "amount": 15000,
                        "bank_trans_id": "manual-bank-tx",
                        "description": "Manual settlement",
                        "sender_account": "123456",
                        "sender_bank": "VCB",
                        "status": "success",
                    },
                ),
                201,
                "POST /api/transactions",
            )
            state["manual_transaction_id"] = payload["data"]["transaction_id"]
            expect_status(client.get("/api/transactions", headers=auth_header(token)), 200, "GET /api/transactions")
            expect_status(
                client.get(f"/api/transactions/{state['manual_transaction_id']}", headers=auth_header(token)),
                200,
                "GET /api/transactions/<id>",
            )

            step("Stats and logs")
            payload = expect_status(client.get("/api/stats", headers=auth_header(token)), 200, "GET /api/stats")
            ensure(payload["data"]["monthly_revenue"] > 0, "Stats monthly revenue should be positive")
            ensure(payload["data"]["best_product"]["product_id"] == state["product_id"], "Stats best product mismatch")
            ensure(payload["data"]["top_customer"]["sender_bank"] == "VCB", "Stats top customer mismatch")

            payload = expect_status(client.get("/api/audit-logs", headers=auth_header(token)), 200, "GET /api/audit-logs")
            ensure(payload["meta"]["total"] > 0, "Expected IoT/device audit logs")
            payload = expect_status(client.get("/api/audit-logs/stats", headers=auth_header(token)), 200, "GET /api/audit-logs/stats")
            ensure(payload["data"]["total_requests"] > 0, "Audit log stats total_requests should be positive")

            payload = expect_status(
                client.post(
                    "/api/staff-access",
                    headers=auth_header(token),
                    json={"machine_id": state["machine_1_id"], "action": "maintenance", "note": "Open panel"},
                ),
                201,
                "POST /api/staff-access",
            )
            state["staff_access_id"] = payload["data"]["access_id"]
            expect_status(client.get("/api/staff-access", headers=auth_header(token)), 200, "GET /api/staff-access")
            expect_status(
                client.get(f"/api/staff-access/{state['staff_access_id']}", headers=auth_header(token)),
                200,
                "GET /api/staff-access/<id>",
            )
            expect_status(
                client.put(
                    f"/api/staff-access/{state['staff_access_id']}/close",
                    headers=auth_header(token),
                    json={"note": "Closed panel"},
                ),
                200,
                "PUT /api/staff-access/<id>/close",
            )

            payload = expect_status(client.get("/api/admin-logs", headers=auth_header(token)), 200, "GET /api/admin-logs")
            ensure(payload["meta"]["total"] > 0, "Expected admin activity logs")
            payload = expect_status(client.get("/api/admin-logs/stats", headers=auth_header(token)), 200, "GET /api/admin-logs/stats")
            ensure(payload["data"]["total_actions"] > 0, "Admin log stats total_actions should be positive")

            step("Firmware flow")
            with patch("app.utils.mqtt.send_machine_command", return_value=True):
                payload = expect_status(
                    client.post(
                        "/api/firmware/updates",
                        headers=auth_header(token),
                        json={
                            "machine_id": state["machine_1_id"],
                            "to_version": "2.0.0",
                            "from_version": "1.0.0",
                            "file_url": "http://example.com/fw.bin",
                            "checksum": "checksum-123",
                        },
                    ),
                    200,
                    "POST /api/firmware/updates",
                )
            ensure(len(payload["data"]) == 1, "Expected one firmware update record")
            state["firmware_update_id"] = payload["data"][0]["update_id"]
            expect_status(client.get("/api/firmware/updates", headers=auth_header(token)), 200, "GET /api/firmware/updates")
            expect_status(
                client.post(
                    "/api/firmware/report-progress",
                    headers=machine_header(machine_1["secret_key"]),
                    json={"update_id": state["firmware_update_id"], "progress": 100, "status": "completed"},
                ),
                200,
                "POST /api/firmware/report-progress",
            )
            firmware_update = db.session.get(FirmwareUpdate, state["firmware_update_id"])
            ensure(firmware_update.status == "completed", "Firmware progress did not update status")
            expect_status(
                client.delete(
                    f"/api/firmware/updates/{state['firmware_update_id']}",
                    headers=auth_header(token),
                ),
                200,
                "DELETE /api/firmware/updates/<id>",
            )

            step("Error handling")
            payload = expect_status(client.get("/api/test/boom"), 500, "GET /api/test/boom")
            ensure(payload["message"] == "An internal server error occurred", "Generic error handler leaked details")
            ensure("sensitive internal detail" not in json.dumps(payload), "Exception detail leaked to response")

            step("Final DB consistency checks")
            ensure(DeviceIdentity.query.count() >= 1, "Expected at least one device identity in DB")
            ensure(DeviceSession.query.count() >= 1, "Expected at least one device session in DB")
            ensure(Transaction.query.count() >= 2, "Expected at least two transactions in DB")

            print("[PASS] Backend full flow integration scenario completed")
            return 0
    finally:
        try:
            os.unlink(DB_FILE.name)
        except OSError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise

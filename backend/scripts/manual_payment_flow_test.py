#!/usr/bin/env python3
"""
Manual integration test for the online payment flow.

This script exercises the main backend endpoints in sequence:
1. Create a pending order
2. Create a PayOS payment link
3. Optionally cancel the payment
4. Simulate a successful webhook
5. Verify payment status
6. Check pending dispense orders for the machine
7. Optionally mark dispense complete
8. Inspect debug DB endpoint

Examples:
    python backend/scripts/manual_payment_flow_test.py \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1

    python backend/scripts/manual_payment_flow_test.py \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1 \
      --machine-key maybanhang-v3 \
      --slot-code A1 \
      --complete-dispense

    python backend/scripts/manual_payment_flow_test.py \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1 \
      --test-cancel
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


def pretty(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


class StepError(RuntimeError):
    pass


class FlowTester:
    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        *,
        expected_status: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            timeout=self.timeout,
        )

        try:
            payload = response.json()
        except ValueError:
            raise StepError(
                f"{method} {path} returned non-JSON response with status {response.status_code}:\n"
                f"{response.text}"
            )

        print(f"\n[{method} {path}] HTTP {response.status_code}")
        print(pretty(payload))

        if expected_status is not None and response.status_code != expected_status:
            raise StepError(
                f"{method} {path} expected HTTP {expected_status}, got {response.status_code}"
            )

        return payload


def create_pending_order(
    tester: FlowTester,
    product_id: int,
    price: int,
    slot_id: Optional[int],
) -> Dict[str, Any]:
    payload = {
        "product_id": product_id,
        "price_snapshot": price,
    }
    if slot_id is not None:
        payload["slot_id"] = slot_id

    result = tester.request(
        "POST",
        "/api/orders/pending",
        expected_status=201,
        headers={"Content-Type": "application/json"},
        json_body=payload,
    )

    order = result.get("data") or {}
    order_id = order.get("order_id")
    if not order_id:
        raise StepError("Create pending order did not return order_id")
    if order.get("status_payment") != "pending":
        raise StepError("New order is not in pending payment state")
    return order


def create_payment_link(
    tester: FlowTester,
    order_id: int,
    amount: int,
    item_name: str,
) -> Dict[str, Any]:
    payload = {
        "order_code": order_id,
        "amount": amount,
        "description": f"Thanh toan don hang #{order_id}",
        "items": [
            {
                "name": item_name,
                "quantity": 1,
                "price": amount,
            }
        ],
    }

    result = tester.request(
        "POST",
        "/api/payment/create",
        expected_status=201,
        headers={"Content-Type": "application/json"},
        json_body=payload,
    )

    data = result.get("data") or {}
    if not data.get("payment_code"):
        raise StepError("Payment link response did not include payment_code")
    return data


def simulate_success_webhook(
    tester: FlowTester,
    payment_code: int,
    amount: int,
) -> Dict[str, Any]:
    payload = {
        "code": "00",
        "desc": "success",
        "success": True,
        "data": {
            "orderCode": payment_code,
            "amount": amount,
            "description": f"Thanh toan don hang #{payment_code}",
            "reference": f"TEST-{payment_code}",
        },
    }
    return tester.request(
        "POST",
        "/api/payment/webhook",
        expected_status=200,
        headers={"Content-Type": "application/json"},
        json_body=payload,
    )


def fetch_order_status(tester: FlowTester, order_id: int) -> Dict[str, Any]:
    result = tester.request(
        "GET",
        f"/api/orders/{order_id}/status",
        expected_status=200,
    )
    return result.get("data") or {}


def fetch_payment_status(tester: FlowTester, payment_code: int) -> Dict[str, Any]:
    result = tester.request(
        "GET",
        f"/api/payment/status/{payment_code}",
        expected_status=200,
    )
    return result.get("data") or {}


def cancel_payment(tester: FlowTester, payment_code: int) -> Dict[str, Any]:
    return tester.request(
        "POST",
        f"/api/payment/cancel/{payment_code}",
        expected_status=200,
    )


def check_pending_orders(tester: FlowTester, machine_key: str) -> Dict[str, Any]:
    return tester.request(
        "GET",
        "/api/iot/pending-orders",
        expected_status=200,
        headers={"X-Machine-Key": machine_key},
    )


def complete_dispense(
    tester: FlowTester,
    machine_key: str,
    order_id: int,
    slot_code: str,
) -> Dict[str, Any]:
    return tester.request(
        "POST",
        "/api/iot/dispense-complete",
        expected_status=200,
        headers={
            "Content-Type": "application/json",
            "X-Machine-Key": machine_key,
        },
        json_body={
            "order_id": order_id,
            "slot_code": slot_code,
            "success": True,
            "message": "Dispensed from manual test script",
        },
    )


def debug_db(tester: FlowTester) -> Dict[str, Any]:
    return tester.request(
        "GET",
        "/api/debug-db",
        expected_status=200,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual test for online payment flow")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Backend base URL")
    parser.add_argument("--product-id", type=int, required=True, help="Product ID to create the order for")
    parser.add_argument("--price", type=int, required=True, help="Expected order amount")
    parser.add_argument("--slot-id", type=int, default=None, help="Slot ID for the pending order")
    parser.add_argument("--item-name", default="Manual Test Item", help="Item name sent to payment/create")
    parser.add_argument("--machine-key", default=None, help="Machine key for IoT endpoints")
    parser.add_argument("--slot-code", default=None, help="Slot code for dispense-complete")
    parser.add_argument(
        "--test-cancel",
        action="store_true",
        help="Cancel payment after link creation and stop after cancel verification",
    )
    parser.add_argument(
        "--complete-dispense",
        action="store_true",
        help="Call /iot/dispense-complete after checking pending orders",
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tester = FlowTester(args.base_url, timeout=args.timeout)

    try:
        print("== Step 1: Create pending order ==")
        order = create_pending_order(tester, args.product_id, args.price, args.slot_id)
        order_id = int(order["order_id"])

        print("\n== Step 2: Create payment link ==")
        payment_data = create_payment_link(tester, order_id, args.price, args.item_name)
        payment_code = int(payment_data["payment_code"])

        print("\nSummary after payment link creation")
        print(f"order_id={order_id}")
        print(f"payment_code={payment_code}")
        print(f"checkout_url={payment_data.get('checkout_url')}")

        if args.test_cancel:
            print("\n== Step 3: Cancel payment ==")
            cancel_payment(tester, payment_code)

            print("\n== Step 4: Verify order status after cancel ==")
            order_status = fetch_order_status(tester, order_id)
            if order_status.get("status_payment") != "cancelled":
                raise StepError("Order was not marked as cancelled after payment cancel")

            print("\nCancel flow test completed successfully.")
            return 0

        print("\n== Step 3: Simulate successful webhook ==")
        simulate_success_webhook(tester, payment_code, args.price)

        print("\n== Step 4: Verify duplicate webhook is ignored ==")
        duplicate = simulate_success_webhook(tester, payment_code, args.price)
        if duplicate.get("message") != "Webhook này đã được xử lý trước đó":
            raise StepError("Duplicate webhook did not return the expected dedup message")

        print("\n== Step 5: Verify order status ==")
        order_status = fetch_order_status(tester, order_id)
        if order_status.get("status_payment") != "completed":
            raise StepError("Order status_payment is not completed after webhook")
        if order_status.get("status_slots") != "pending":
            raise StepError("Order status_slots is not pending after payment completion")

        print("\n== Step 6: Verify payment status endpoint ==")
        payment_status = fetch_payment_status(tester, payment_code)
        if str(payment_status.get("status", "")).upper() not in {"PAID", "SUCCESS", "COMPLETED", ""}:
            print("Warning: PayOS status is not one of the expected paid values in this local test.")

        if args.machine_key:
            print("\n== Step 7: Check pending orders for machine ==")
            pending_orders = check_pending_orders(tester, args.machine_key)
            pending_items = pending_orders.get("data") or []
            if not any(int(item.get("order_id", 0)) == order_id for item in pending_items):
                raise StepError("Order is not present in /iot/pending-orders after payment completion")

            if args.complete_dispense:
                if not args.slot_code:
                    raise StepError("--slot-code is required when using --complete-dispense")

                print("\n== Step 8: Mark dispense complete ==")
                complete_dispense(tester, args.machine_key, order_id, args.slot_code)

                print("\n== Step 9: Verify order status after dispense ==")
                order_status = fetch_order_status(tester, order_id)
                if order_status.get("status_slots") != "dispensed":
                    raise StepError("Order status_slots is not dispensed after dispense-complete")

        print("\n== Debug snapshot ==")
        debug_db(tester)

        print("\nManual payment flow test completed successfully.")
        return 0

    except StepError as exc:
        print(f"\nTEST FAILED: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"\nHTTP ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

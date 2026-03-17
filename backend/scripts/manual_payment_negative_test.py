#!/usr/bin/env python3
"""
Manual negative/regression tests for the online payment flow.

This script covers failure cases that should now be handled safely:
1. Payment creation with mismatched amount
2. Payment creation for a non-pending order
3. Cancel payment then verify DB status
4. Webhook after cancel must not mark order completed
5. Duplicate webhook payload must be ignored

Examples:
    python backend/scripts/manual_payment_negative_test.py \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1
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
) -> int:
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
    order_id = (result.get("data") or {}).get("order_id")
    if not order_id:
        raise StepError("Could not create pending order")
    return int(order_id)


def create_payment(
    tester: FlowTester,
    order_id: int,
    amount: int,
    *,
    expected_status: int,
    item_name: str = "Negative Test Item",
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
    return tester.request(
        "POST",
        "/api/payment/create",
        expected_status=expected_status,
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


def cancel_payment(tester: FlowTester, payment_code: int) -> Dict[str, Any]:
    return tester.request(
        "POST",
        f"/api/payment/cancel/{payment_code}",
        expected_status=200,
    )


def simulate_success_webhook(
    tester: FlowTester,
    payment_code: int,
    amount: int,
    *,
    expected_status: int,
) -> Dict[str, Any]:
    payload = {
        "code": "00",
        "desc": "success",
        "success": True,
        "data": {
            "orderCode": payment_code,
            "amount": amount,
            "description": f"Thanh toan don hang #{payment_code}",
            "reference": f"NEG-{payment_code}",
        },
    }
    return tester.request(
        "POST",
        "/api/payment/webhook",
        expected_status=expected_status,
        headers={"Content-Type": "application/json"},
        json_body=payload,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual negative tests for online payment flow")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Backend base URL")
    parser.add_argument("--product-id", type=int, required=True, help="Product ID to create the order for")
    parser.add_argument("--price", type=int, required=True, help="Expected order amount")
    parser.add_argument("--slot-id", type=int, default=None, help="Slot ID for the pending order")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tester = FlowTester(args.base_url, timeout=args.timeout)

    try:
        print("== Case 1: payment/create with wrong amount must fail ==")
        order_id_wrong_amount = create_pending_order(tester, args.product_id, args.price, args.slot_id)
        wrong_amount_resp = create_payment(
            tester,
            order_id_wrong_amount,
            args.price + 1,
            expected_status=400,
        )
        if "không khớp" not in str(wrong_amount_resp.get("message", "")):
            raise StepError("Wrong amount case did not return mismatch message")

        print("\n== Case 2: cancel payment then order must be cancelled ==")
        order_id_cancel = create_pending_order(tester, args.product_id, args.price, args.slot_id)
        payment_resp = create_payment(
            tester,
            order_id_cancel,
            args.price,
            expected_status=201,
        )
        payment_code = int((payment_resp.get("data") or {}).get("payment_code", 0))
        if not payment_code:
            raise StepError("Could not obtain payment_code for cancel case")

        cancel_payment(tester, payment_code)
        cancelled_status = fetch_order_status(tester, order_id_cancel)
        if cancelled_status.get("status_payment") != "cancelled":
            raise StepError("Order was not marked cancelled after cancel endpoint")

        print("\n== Case 3: webhook after cancel must be rejected ==")
        webhook_after_cancel = simulate_success_webhook(
            tester,
            payment_code,
            args.price,
            expected_status=409,
        )
        if "đã bị hủy" not in str(webhook_after_cancel.get("message", "")):
            raise StepError("Webhook-after-cancel did not return cancelled message")

        cancelled_status = fetch_order_status(tester, order_id_cancel)
        if cancelled_status.get("status_payment") != "cancelled":
            raise StepError("Webhook-after-cancel changed cancelled order state unexpectedly")

        print("\n== Case 4: completed order must reject new payment/create ==")
        order_id_completed = create_pending_order(tester, args.product_id, args.price, args.slot_id)
        completed_payment_resp = create_payment(
            tester,
            order_id_completed,
            args.price,
            expected_status=201,
        )
        completed_payment_code = int((completed_payment_resp.get("data") or {}).get("payment_code", 0))
        if not completed_payment_code:
            raise StepError("Could not obtain payment_code for completed case")

        first_webhook = simulate_success_webhook(
            tester,
            completed_payment_code,
            args.price,
            expected_status=200,
        )
        if "thành công" not in str(first_webhook.get("message", "")).lower():
            raise StepError("First webhook did not succeed as expected")

        status_after_complete = fetch_order_status(tester, order_id_completed)
        if status_after_complete.get("status_payment") != "completed":
            raise StepError("Order was not completed after success webhook")

        non_pending_resp = create_payment(
            tester,
            order_id_completed,
            args.price,
            expected_status=409,
        )
        if "không ở trạng thái chờ thanh toán" not in str(non_pending_resp.get("message", "")):
            raise StepError("Completed order did not reject new payment/create correctly")

        print("\n== Case 5: duplicate webhook must be ignored safely ==")
        duplicate_resp = simulate_success_webhook(
            tester,
            completed_payment_code,
            args.price,
            expected_status=200,
        )
        if "đã được xử lý trước đó" not in str(duplicate_resp.get("message", "")):
            raise StepError("Duplicate webhook did not return dedup message")

        status_after_duplicate = fetch_order_status(tester, order_id_completed)
        if status_after_duplicate.get("status_payment") != "completed":
            raise StepError("Duplicate webhook changed completed order state unexpectedly")

        print("\nNegative payment tests completed successfully.")
        return 0

    except StepError as exc:
        print(f"\nTEST FAILED: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"\nHTTP ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

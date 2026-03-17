#!/usr/bin/env python3
"""
Unified manual test runner for the online payment flow.

Modes:
  - success: run the happy-path integration flow
  - negative: run failure/regression scenarios
  - all: run both in sequence

Examples:
    python backend/scripts/manual_payment_test_suite.py \
      --mode all \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1

    python backend/scripts/manual_payment_test_suite.py \
      --mode success \
      --base-url http://localhost:5000 \
      --product-id 1 \
      --price 10000 \
      --slot-id 1 \
      --machine-key maybanhang-v3 \
      --slot-code A1 \
      --complete-dispense
"""

from __future__ import annotations

import argparse
import sys

import manual_payment_flow_test as success_test
import manual_payment_negative_test as negative_test


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified manual payment test suite")
    parser.add_argument(
        "--mode",
        choices=["success", "negative", "all"],
        default="all",
        help="Which test set to run",
    )
    parser.add_argument("--base-url", default="http://localhost:5000", help="Backend base URL")
    parser.add_argument("--product-id", type=int, required=True, help="Product ID to create the order for")
    parser.add_argument("--price", type=int, required=True, help="Expected order amount")
    parser.add_argument("--slot-id", type=int, default=None, help="Slot ID for the pending order")
    parser.add_argument("--item-name", default="Manual Test Item", help="Item name sent to payment/create")
    parser.add_argument("--machine-key", default=None, help="Machine key for IoT endpoints in success mode")
    parser.add_argument("--slot-code", default=None, help="Slot code for dispense-complete in success mode")
    parser.add_argument(
        "--complete-dispense",
        action="store_true",
        help="Call /iot/dispense-complete in success mode",
    )
    parser.add_argument(
        "--test-cancel",
        action="store_true",
        help="Run cancel branch inside success mode instead of full paid flow",
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    return parser.parse_args()


def run_success(args: argparse.Namespace) -> None:
    tester = success_test.FlowTester(args.base_url, timeout=args.timeout)

    print("==== SUCCESS FLOW ====")
    order = success_test.create_pending_order(tester, args.product_id, args.price, args.slot_id)
    order_id = int(order["order_id"])

    payment_data = success_test.create_payment_link(tester, order_id, args.price, args.item_name)
    payment_code = int(payment_data["payment_code"])

    print("\nSummary after payment link creation")
    print(f"order_id={order_id}")
    print(f"payment_code={payment_code}")
    print(f"checkout_url={payment_data.get('checkout_url')}")

    if args.test_cancel:
        success_test.cancel_payment(tester, payment_code)
        order_status = success_test.fetch_order_status(tester, order_id)
        if order_status.get("status_payment") != "cancelled":
            raise success_test.StepError("Order was not marked as cancelled after payment cancel")
        print("\nSuccess-mode cancel branch completed successfully.")
        return

    success_test.simulate_success_webhook(tester, payment_code, args.price)

    duplicate = success_test.simulate_success_webhook(tester, payment_code, args.price)
    if duplicate.get("message") != "Webhook này đã được xử lý trước đó":
        raise success_test.StepError("Duplicate webhook did not return the expected dedup message")

    order_status = success_test.fetch_order_status(tester, order_id)
    if order_status.get("status_payment") != "completed":
        raise success_test.StepError("Order status_payment is not completed after webhook")
    if order_status.get("status_slots") != "pending":
        raise success_test.StepError("Order status_slots is not pending after payment completion")

    success_test.fetch_payment_status(tester, payment_code)

    if args.machine_key:
        pending_orders = success_test.check_pending_orders(tester, args.machine_key)
        pending_items = pending_orders.get("data") or []
        if not any(int(item.get("order_id", 0)) == order_id for item in pending_items):
            raise success_test.StepError("Order is not present in /iot/pending-orders after payment completion")

        if args.complete_dispense:
            if not args.slot_code:
                raise success_test.StepError("--slot-code is required when using --complete-dispense")
            success_test.complete_dispense(tester, args.machine_key, order_id, args.slot_code)
            order_status = success_test.fetch_order_status(tester, order_id)
            if order_status.get("status_slots") != "dispensed":
                raise success_test.StepError("Order status_slots is not dispensed after dispense-complete")

    success_test.debug_db(tester)
    print("\nSuccess flow completed successfully.")


def run_negative(args: argparse.Namespace) -> None:
    tester = negative_test.FlowTester(args.base_url, timeout=args.timeout)

    print("==== NEGATIVE FLOW ====")

    order_id_wrong_amount = negative_test.create_pending_order(tester, args.product_id, args.price, args.slot_id)
    wrong_amount_resp = negative_test.create_payment(
        tester,
        order_id_wrong_amount,
        args.price + 1,
        expected_status=400,
    )
    if "không khớp" not in str(wrong_amount_resp.get("message", "")):
        raise negative_test.StepError("Wrong amount case did not return mismatch message")

    order_id_cancel = negative_test.create_pending_order(tester, args.product_id, args.price, args.slot_id)
    payment_resp = negative_test.create_payment(
        tester,
        order_id_cancel,
        args.price,
        expected_status=201,
    )
    payment_code = int((payment_resp.get("data") or {}).get("payment_code", 0))
    if not payment_code:
        raise negative_test.StepError("Could not obtain payment_code for cancel case")

    negative_test.cancel_payment(tester, payment_code)
    cancelled_status = negative_test.fetch_order_status(tester, order_id_cancel)
    if cancelled_status.get("status_payment") != "cancelled":
        raise negative_test.StepError("Order was not marked cancelled after cancel endpoint")

    webhook_after_cancel = negative_test.simulate_success_webhook(
        tester,
        payment_code,
        args.price,
        expected_status=409,
    )
    if "đã bị hủy" not in str(webhook_after_cancel.get("message", "")):
        raise negative_test.StepError("Webhook-after-cancel did not return cancelled message")

    cancelled_status = negative_test.fetch_order_status(tester, order_id_cancel)
    if cancelled_status.get("status_payment") != "cancelled":
        raise negative_test.StepError("Webhook-after-cancel changed cancelled order state unexpectedly")

    order_id_completed = negative_test.create_pending_order(tester, args.product_id, args.price, args.slot_id)
    completed_payment_resp = negative_test.create_payment(
        tester,
        order_id_completed,
        args.price,
        expected_status=201,
        item_name=args.item_name,
    )
    completed_payment_code = int((completed_payment_resp.get("data") or {}).get("payment_code", 0))
    if not completed_payment_code:
        raise negative_test.StepError("Could not obtain payment_code for completed case")

    first_webhook = negative_test.simulate_success_webhook(
        tester,
        completed_payment_code,
        args.price,
        expected_status=200,
    )
    if "thành công" not in str(first_webhook.get("message", "")).lower():
        raise negative_test.StepError("First webhook did not succeed as expected")

    status_after_complete = negative_test.fetch_order_status(tester, order_id_completed)
    if status_after_complete.get("status_payment") != "completed":
        raise negative_test.StepError("Order was not completed after success webhook")

    non_pending_resp = negative_test.create_payment(
        tester,
        order_id_completed,
        args.price,
        expected_status=409,
        item_name=args.item_name,
    )
    if "không ở trạng thái chờ thanh toán" not in str(non_pending_resp.get("message", "")):
        raise negative_test.StepError("Completed order did not reject new payment/create correctly")

    duplicate_resp = negative_test.simulate_success_webhook(
        tester,
        completed_payment_code,
        args.price,
        expected_status=200,
    )
    if "đã được xử lý trước đó" not in str(duplicate_resp.get("message", "")):
        raise negative_test.StepError("Duplicate webhook did not return dedup message")

    status_after_duplicate = negative_test.fetch_order_status(tester, order_id_completed)
    if status_after_duplicate.get("status_payment") != "completed":
        raise negative_test.StepError("Duplicate webhook changed completed order state unexpectedly")

    print("\nNegative flow completed successfully.")


def main() -> int:
    args = parse_args()

    try:
        if args.mode in {"success", "all"}:
            run_success(args)

        if args.mode in {"negative", "all"}:
            run_negative(args)

        print("\nManual payment test suite completed successfully.")
        return 0
    except (success_test.StepError, negative_test.StepError) as exc:
        print(f"\nTEST FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

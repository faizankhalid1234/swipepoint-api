"""
Normalize SwipePoint charge API responses into a stable client shape.

2D (approved inline): data.transaction { status, message }
3DS (redirect):       data.link
"""

from __future__ import annotations

from typing import Any

from .models import TransactionStatus


def _order_id(data: dict) -> str:
    v = data.get("orderid") or data.get("orderId") or data.get("order_id")
    if v is None:
        return ""
    return str(v)


def _as_dict(body: Any) -> dict | None:
    return body if isinstance(body, dict) else None


def build_charge_client_response(
    *,
    reference: str,
    provider_http_status: int,
    provider_body: Any,
) -> tuple[dict, int, str]:
    """
    Returns (response_json, http_status_for_client, transaction_status_for_db).

    Client JSON matches:
      - 2D: status/message + data.reference, orderid, transaction{status,message}
      - 3DS: status/message + data.reference, orderid, link
      - failed: status failed + data.reference (+ orderid when known)
    """
    # Transport / parse failure
    if provider_http_status == 0:
        msg = "Payment gateway unreachable"
        if isinstance(provider_body, dict) and provider_body.get("error"):
            msg = str(provider_body["error"])
        return (
            {
                "status": "failed",
                "message": msg,
                "data": {"reference": reference, "orderid": ""},
            },
            502,
            TransactionStatus.FAILED,
        )

    raw = _as_dict(provider_body)
    if raw is None:
        return (
            {
                "status": "failed",
                "message": "Invalid response from payment gateway",
                "data": {"reference": reference, "orderid": ""},
            },
            502,
            TransactionStatus.FAILED,
        )

    top_status = (raw.get("status") or "").lower()
    message = raw.get("message")
    if message is None or message == "":
        message = (
            "success" if top_status == "success" else (raw.get("error") or "failed")
        )

    data = raw.get("data")
    if not isinstance(data, dict):
        data = {}

    # Some gateways put link / orderid on the root object
    if isinstance(raw.get("link"), str) and raw["link"].strip() and "link" not in data:
        data = {**data, "link": raw["link"].strip()}
    for key in ("orderid", "orderId", "order_id"):
        if key in raw and raw[key] and not _order_id(data):
            data = {**data, "orderid": raw[key]}
            break

    ref = data.get("reference") or reference
    oid = _order_id(data)

    # --- Failure from gateway (HTTP or body) ---
    body_failed = (
        top_status in ("failed", "error", "declined") or raw.get("success") is False
    )
    if not (200 <= provider_http_status < 300) or body_failed:
        err_msg = message
        if isinstance(raw.get("data"), dict) and raw["data"].get("message"):
            err_msg = str(raw["data"]["message"])
        elif raw.get("errors"):
            err_msg = str(raw.get("errors"))
        return (
            {
                "status": "failed",
                "message": err_msg,
                "data": {"reference": ref, "orderid": oid},
            },
            200 if 200 <= provider_http_status < 500 else 502,
            TransactionStatus.FAILED,
        )

    # --- 3DS: redirect link ---
    link = data.get("link")
    if isinstance(link, str) and link.strip():
        return (
            {
                "status": "success",
                "message": "success",
                "data": {
                    "reference": ref,
                    "orderid": oid,
                    "link": link.strip(),
                },
            },
            200,
            TransactionStatus.AWAITING_3DS,
        )

    # --- 2D: inline transaction result ---
    trans = data.get("transaction")
    if isinstance(trans, dict):
        t_status = (trans.get("status") or "success").lower()
        t_msg = trans.get("message") or "Transaction is approved"
        if t_status != "success":
            return (
                {
                    "status": "failed",
                    "message": t_msg,
                    "data": {"reference": ref, "orderid": oid},
                },
                200,
                TransactionStatus.FAILED,
            )
        return (
            {
                "status": "success",
                "message": "success",
                "data": {
                    "reference": ref,
                    "orderid": oid,
                    "transaction": {
                        "status": "success",
                        "message": t_msg,
                    },
                },
            },
            200,
            TransactionStatus.SUCCESS,
        )

    # Success at top level but no transaction/link — pass through minimal 2D
    if top_status == "success":
        return (
            {
                "status": "success",
                "message": "success",
                "data": {
                    "reference": ref,
                    "orderid": oid,
                    "transaction": {
                        "status": "success",
                        "message": "Transaction is approved",
                    },
                },
            },
            200,
            TransactionStatus.SUCCESS,
        )

    return (
        {
            "status": "failed",
            "message": message,
            "data": {"reference": ref, "orderid": oid},
        },
        200,
        TransactionStatus.FAILED,
    )

from __future__ import annotations

import logging
import random
import string
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _generate_order_id() -> str:
    return str(random.randint(1000000, 9999999))


def _generate_3ds_link(reference: str) -> str:
    token = "".join(random.choices(string.ascii_letters + string.digits, k=28))
    return f"https://swipepointe.com/checkout/{reference}/{token}"


def _post_charge_to_internal_gateway(payload: dict[str, Any]) -> tuple[int, dict]:
    """
    Local processor (your own API behavior):
    - CVV == 000      -> failed
    - card ends with 3 -> 3DS (link)
    - else            -> 2D success
    """
    reference = str(payload.get("reference", ""))
    order_id = _generate_order_id()
    card_number = str(payload.get("cardNumber", ""))
    card_cvv = str(payload.get("cardCVV", ""))

    if card_cvv == "000":
        return 200, {
            "status": "failed",
            "message": "Transaction declined",
            "data": {
                "reference": reference,
                "orderid": order_id,
            },
        }

    if card_number and card_number[-1] == "3":
        return 200, {
            "status": "success",
            "message": "success",
            "data": {
                "reference": reference,
                "orderid": order_id,
                "link": _generate_3ds_link(reference),
            },
        }

    return 200, {
        "status": "success",
        "message": "success",
        "data": {
            "reference": reference,
            "orderid": order_id,
            "transaction": {
                "status": "success",
                "message": "Transaction is approved",
            },
        },
    }


def post_charge_to_swipepoint(payload: dict[str, Any]) -> tuple[int, dict | list | str | None]:
    """
    POST JSON to SwipePoint charge API.
    Returns (http_status, parsed_json_or_text).
    """
    provider_mode = getattr(settings, "PAYMENT_PROVIDER_MODE", "internal").lower().strip()
    if provider_mode == "internal":
        return _post_charge_to_internal_gateway(payload)

    url = getattr(settings, "SWIPEPOINT_CHARGE_URL", "https://swipepointe.com/api/charge")
    secret = getattr(settings, "SWIPEPOINT_API_SECRET", "") or ""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret}",
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60)
    except requests.RequestException as e:
        logger.exception("SwipePoint request failed: %s", e)
        return 0, {"error": str(e)}

    ct = r.headers.get("Content-Type", "")
    body: dict | list | str | None
    try:
        if "application/json" in ct:
            body = r.json()
        else:
            body = r.text[:8000] if r.text else None
    except ValueError:
        body = r.text[:8000] if r.text else None

    return r.status_code, body

"""Build a DB-safe snapshot of the charge request (PCI: no full PAN, no CVV)."""

from __future__ import annotations

import re
from typing import Any


def _last4(card_number: str) -> str:
    digits = re.sub(r"\D", "", card_number or "")
    return digits[-4:] if len(digits) >= 4 else ""


def build_swipepoint_data_snapshot(validated: dict[str, Any]) -> dict[str, Any]:
    """Same keys as POST /api/charge; sensitive values masked."""
    last4 = _last4(str(validated.get("cardNumber") or ""))
    out: dict[str, Any] = {
        "amount": validated["amount"],
        "currency": validated["currency"],
        "reference": validated["reference"],
        "firstname": validated["firstname"],
        "lastname": validated["lastname"],
        "email": validated["email"],
        "phone": validated["phone"],
        "cardName": validated["cardName"],
        "cardNumber": f"************{last4}" if last4 else "****",
        "cardCVV": "[redacted]",
        "expMonth": validated["expMonth"],
        "expYear": validated["expYear"],
        "country": validated["country"],
        "city": validated["city"],
        "address": validated["address"],
        "ip_address": validated["ip_address"],
        "zip_code": validated["zip_code"],
        "state": validated["state"],
        "callback_url": validated["callback_url"],
    }
    wu = validated.get("webhook_url")
    if wu:
        out["webhook_url"] = wu
    return out

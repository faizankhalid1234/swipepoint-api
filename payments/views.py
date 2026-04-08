from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction as db_transaction
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .charge_response import build_charge_client_response
from .models import Transaction, TransactionStatus
from .request_snapshot import build_swipepoint_data_snapshot
from .serializers import ChargeSerializer
from .services import post_charge_to_swipepoint


class HomeView(APIView):
    """GET / — API info (avoids 404 on root URL)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "service": "SwipePoint backend",
                "version": "1.0",
                "endpoints": {
                    "GET /health/": "Load balancer / platform health check",
                    "POST /api/charge": "Payment charge (JSON body per SwipePoint spec)",
                    "GET /admin/": "Django admin",
                },
            }
        )


class HealthView(APIView):
    """GET /health/ — returns 200 when the app is up (for Railway, Render, etc.)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"})


def _card_last4(card_number: str) -> str:
    digits = re.sub(r"\D", "", card_number or "")
    return digits[-4:] if len(digits) >= 4 else ""


def _build_swipepoint_payload(validated: dict) -> dict:
    """Exact JSON keys expected by SwipePoint."""
    out = {
        "amount": validated["amount"],
        "currency": validated["currency"],
        "reference": validated["reference"],
        "firstname": validated["firstname"],
        "lastname": validated["lastname"],
        "email": validated["email"],
        "phone": validated["phone"],
        "cardName": validated["cardName"],
        "cardNumber": validated["cardNumber"],
        "cardCVV": validated["cardCVV"],
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


class ChargeView(APIView):
    """
    POST /api/charge
    Accepts JSON body per SwipePoint spec. Merchant Bearer token is taken from env, not from client.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        provider_mode = (
            getattr(settings, "PAYMENT_PROVIDER_MODE", "internal").lower().strip()
        )
        if provider_mode != "internal" and not getattr(
            settings, "SWIPEPOINT_API_SECRET", None
        ):
            return Response(
                {
                    "detail": "Server misconfiguration: SWIPEPOINT_API_SECRET is not set."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ser = ChargeSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        v = ser.validated_data
        try:
            Decimal(str(v["amount"].strip()))
        except (InvalidOperation, AttributeError):
            return Response(
                {"amount": ["Must be a valid decimal amount string."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = _build_swipepoint_payload(v)

        try:
            with db_transaction.atomic():
                txn = Transaction.objects.create(
                    reference=v["reference"],
                    amount=v["amount"].strip(),
                    currency=v["currency"],
                    firstname=v["firstname"],
                    lastname=v["lastname"],
                    email=v["email"],
                    phone=v["phone"],
                    card_name=v["cardName"],
                    card_last4=_card_last4(v["cardNumber"]),
                    exp_month=v["expMonth"],
                    exp_year=v["expYear"],
                    country=v["country"],
                    city=v["city"],
                    address=v["address"],
                    zip_code=v["zip_code"],
                    state=v["state"],
                    ip_address=v["ip_address"],
                    callback_url=v["callback_url"],
                    webhook_url=(v.get("webhook_url") or "").strip() or None,
                    status=TransactionStatus.PENDING,
                    swipepoint_data=build_swipepoint_data_snapshot(v),
                )

                http_status, body = post_charge_to_swipepoint(payload)

                txn.provider_status_code = http_status if http_status else None
                txn.provider_response = (
                    body if isinstance(body, (dict, list)) else {"raw": body}
                )

                client_body, client_http, txn_status = build_charge_client_response(
                    reference=txn.reference,
                    provider_http_status=http_status,
                    provider_body=body,
                )
                txn.status = txn_status
                txn.error_message = ""
                if txn_status == TransactionStatus.FAILED:
                    txn.error_message = str(client_body.get("message") or "")[:2000]

                txn.save(
                    update_fields=[
                        "status",
                        "provider_status_code",
                        "provider_response",
                        "error_message",
                        "updated_at",
                    ]
                )

        except IntegrityError:
            return Response(
                {"reference": ["A transaction with this reference already exists."]},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(client_body, status=client_http)

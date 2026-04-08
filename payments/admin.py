import json

from django.contrib import admin
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .charge_response import build_charge_client_response
from .models import SwipePointData


@admin.register(SwipePointData)
class SwipePointDataAdmin(admin.ModelAdmin):
    """List: short columns. Detail (click): request JSON + same API response as client."""

    list_display = (
        "reference",
        "amount",
        "created_at",
        "display_name",
        "email",
    )
    search_fields = ("reference", "email", "firstname", "lastname")
    ordering = ("-created_at",)
    readonly_fields = (
        "swipepoint_data_formatted",
        "api_response_formatted",
    )

    fieldsets = (
        (
            "Request body (POST /api/charge jaisa)",
            {
                "description": "Sirf detail page par — list par nahi.",
                "fields": ("swipepoint_data_formatted",),
            },
        ),
        (
            "API response (client ko jo milta hai)",
            {
                "description": "Wahi shape: status, message, data (2D / 3DS / failed).",
                "fields": ("api_response_formatted",),
            },
        ),
    )

    @admin.display(description="Name")
    def display_name(self, obj):
        full = f"{obj.firstname} {obj.lastname}".strip()
        return full or obj.card_name or "—"

    @admin.display(description="Body (JSON)")
    def swipepoint_data_formatted(self, obj):
        if not obj.swipepoint_data:
            return "—"
        try:
            pretty = json.dumps(obj.swipepoint_data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(obj.swipepoint_data)
        return mark_safe(
            '<pre style="max-width:900px;white-space:pre-wrap;">'
            + escape(pretty)
            + "</pre>"
        )

    @admin.display(description="API response (JSON)")
    def api_response_formatted(self, obj):
        body, http_code, _ = build_charge_client_response(
            reference=obj.reference,
            provider_http_status=obj.provider_status_code or 0,
            provider_body=obj.provider_response,
        )
        try:
            pretty = json.dumps(body, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            pretty = str(body)
        block = f"HTTP status: {http_code}\n\n{pretty}"
        return mark_safe(
            '<pre style="max-width:900px;white-space:pre-wrap;">'
            + escape(block)
            + "</pre>"
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return request.user.is_staff

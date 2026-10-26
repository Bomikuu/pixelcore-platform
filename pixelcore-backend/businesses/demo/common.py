"""Shared identities, dates and fixture validation for the monthly demonstration."""

import calendar
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from django.core.management.base import CommandError
from django.utils import timezone
from PIL import Image


DATASET = "pixelcore-monthly-demo-v1"
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "monthly_demo" / "dataset.json"
NAMESPACE = uuid.UUID("58ab79c8-a9f6-4f36-9847-f29d55f81c34")
MONEY = Decimal("0.01")
TAX = Decimal("0.12")


def money(value):
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def identity(slug, model, key):
    return uuid.uuid5(NAMESPACE, f"{slug}:{model._meta.label_lower}:{key}")


def load_fixture(path=FIXTURE):
    path = Path(path)
    try:
        data = json.loads(path.read_text())
        if data["schema_version"] != 1 or data["dataset"] != DATASET:
            raise ValueError("Unsupported fixture schema or dataset")
        for name in ("assets", "products", "services", "customers", "staff", "suppliers", "orders",
                     "purchase_orders", "invoices", "quotations", "expenses", "bookings", "events", "leave_requests"):
            rows = data[name]
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"{name} must be a nonempty list")
            keys = [row["key" if name == "assets" else "id"] for row in rows]
            if len(keys) != len(set(keys)):
                raise ValueError(f"Duplicate identifiers in {name}")
        assets = {}
        image_root = (path.parent / "images").resolve()
        for row in data["assets"]:
            source = (image_root / row["file"]).resolve()
            if not source.is_relative_to(image_root):
                raise ValueError("Image paths must stay inside the fixture images directory")
            payload = source.read_bytes()
            with Image.open(source) as image:
                width, height = image.size
                if image.format != "PNG" or min(width, height) < 256:
                    raise ValueError(f"Invalid PNG image: {source.name}")
                image.verify()
            assets[row["key"]] = (row, payload, width, height, hashlib.sha256(payload).hexdigest())
        variants = {f"{p['id']}:{v['id']}" for p in data["products"] for v in p["variants"]}
        customers = {row["id"] for row in data["customers"]}
        services = {row["id"] for row in data["services"]}
        staff = {row["id"] for row in data["staff"]}
        suppliers = {row["id"] for row in data["suppliers"]}
        for row in data["products"]:
            if row["image"] not in assets or money(row["price"]) <= 0 or money(row["cost"]) < 0:
                raise ValueError("Products require an image and valid prices")
        for row in data["orders"] + data["purchase_orders"]:
            for item in row["items"]:
                if item["variant"] not in variants or not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                    raise ValueError("Unknown variant or invalid quantity")
        for row in data["orders"] + data["bookings"] + data["invoices"] + data["quotations"]:
            if row["customer"] not in customers:
                raise ValueError("Unknown customer reference")
        for row in data["bookings"] + data["invoices"] + data["quotations"]:
            if row["service"] not in services:
                raise ValueError("Unknown service reference")
        if any(row["staff"] not in staff for row in data["bookings"] + data["leave_requests"]):
            raise ValueError("Unknown staff reference")
        if any(row["supplier"] not in suppliers for row in data["purchase_orders"]):
            raise ValueError("Unknown supplier reference")
        return data, assets
    except (OSError, KeyError, TypeError, ValueError, ArithmeticError) as exc:
        raise CommandError(f"Invalid monthly fixture: {exc}") from exc


class Context:
    def __init__(self, month, slug, fixture=FIXTURE):
        self.now = timezone.localtime(timezone.now(), ZoneInfo("Asia/Manila"))
        month = month or self.now.strftime("%Y-%m")
        if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
            raise CommandError("Month must use YYYY-MM, for example 2026-10.")
        try:
            self.first = datetime.strptime(month, "%Y-%m").replace(tzinfo=self.now.tzinfo)
        except ValueError as exc:
            raise CommandError("Choose a valid calendar month.") from exc
        if self.first > self.now:
            raise CommandError("Choose the current month or a past month for sample transaction history.")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 80:
            raise CommandError("Use a lowercase demo slug of at most 80 characters.")
        self.month, self.slug = month, slug
        self.days = calendar.monthrange(self.first.year, self.first.month)[1]
        self.history_days = min(self.days, (self.now.date() - self.first.date()).days + 1)
        self.data, self.image_payloads = load_fixture(fixture)
        self.assets, self.products, self.variants, self.costs = {}, {}, {}, {}
        self.customers, self.staff, self.suppliers, self.services = {}, {}, {}, {}
        self.balances, self.invoices = {}, {}

    def monthly(self, key):
        return f"{self.month}:{key}"

    def at(self, day, hour=10, minute=0, history=False):
        if history:
            day = 1 + (min(int(day), 31) - 1) * self.history_days // 31
        at = self.first.replace(day=min(max(int(day), 1), self.days), hour=hour, minute=minute)
        return max(self.first, min(at, self.now)) if history else at

    def save(self, model, key, **fields):
        pk = identity(self.slug, model, key)
        existing = model.objects.filter(public_id=pk).first()
        if existing is not None and hasattr(existing, "business_id") and existing.business_id != self.business.pk:
            raise CommandError("A demo identifier belongs to another business; nothing was imported.")
        obj, _ = model.objects.update_or_create(public_id=pk, defaults=fields)
        return obj

    @staticmethod
    def stamp(obj, **dates):
        type(obj).objects.filter(pk=obj.pk).update(**dates)
        for name, value in dates.items():
            setattr(obj, name, value)
        return obj

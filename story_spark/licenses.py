from __future__ import annotations

import json
import hashlib
import hmac
import os
import urllib.parse
import urllib.request

from .store import LicenseRecord, LicenseStore


def internal_license(provider: str, credential: str) -> str:
    secret = os.getenv("LICENSE_SECRET", "local-development-secret").encode()
    digest = hmac.new(secret, f"{provider}:{credential}".encode(), hashlib.sha256).hexdigest()
    return f"SSS-{digest[:40]}"


def verify_stripe_session(session_id: str) -> bool:
    import stripe

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    session = stripe.checkout.Session.retrieve(session_id, expand=["line_items.data.price", "payment_intent.latest_charge"])
    items = (session.get("line_items") or {}).get("data") or []
    price_id = items[0].get("price", {}).get("id") if len(items) == 1 else None
    charge = (session.get("payment_intent") or {}).get("latest_charge") or {}
    return all((session.get("mode") == "payment", session.get("status") == "complete", session.get("payment_status") == "paid", (session.get("metadata") or {}).get("app") == "story-spark-studio", price_id == os.getenv("STRIPE_PRICE_LIFETIME"), not charge.get("refunded"), not charge.get("disputed")))


def verify_gumroad_key(license_key: str) -> bool:
    data = urllib.parse.urlencode({"product_id": os.environ["GUMROAD_PRODUCT_ID"], "license_key": license_key, "increment_uses_count": "false"}).encode()
    request = urllib.request.Request("https://api.gumroad.com/v2/licenses/verify", data=data)
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.load(response)
    purchase = payload.get("purchase") or {}
    return bool(payload.get("success") and not purchase.get("refunded") and not purchase.get("chargebacked") and purchase.get("product_id") == os.environ["GUMROAD_PRODUCT_ID"])


def verify_payhip_key(license_key: str) -> bool:
    url = "https://payhip.com/api/v2/license/verify?" + urllib.parse.urlencode({"license_key": license_key})
    request = urllib.request.Request(url, headers={"product-secret-key": os.environ["PAYHIP_PRODUCT_SECRET_KEY"]})
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.load(response)
    data = payload.get("data") or {}
    return bool(data.get("enabled") and data.get("product_link") == os.getenv("PAYHIP_PRODUCT_LINK"))


def redeem(store: LicenseStore, provider: str, credential: str, install_id: str) -> tuple[str, LicenseRecord]:
    if provider == "stripe":
        valid = verify_stripe_session(credential)
    elif provider == "gumroad":
        valid = verify_gumroad_key(credential)
    elif provider == "payhip":
        valid = verify_payhip_key(credential)
    else:
        raise ValueError("Choose Stripe, Gumroad, or Payhip.")
    if not valid:
        raise ValueError("That purchase could not be verified for Story Spark Studio.")
    license_key = internal_license(provider, credential)
    return license_key, store.activate(license_key, provider, install_id)

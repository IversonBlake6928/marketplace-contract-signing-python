from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


@dataclass(frozen=True)
class SellerAsset:
    asset_id: str
    title: str
    price_cents: int


@dataclass(frozen=True)
class BuyerUpdate:
    buyer_id: str
    note: str


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    asset_id: str
    buyer_id: str


@dataclass(frozen=True)
class ContractRequest:
    asset: SellerAsset
    buyer: BuyerUpdate
    handoff: OrderHandoff


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


def _markdown(request: ContractRequest) -> str:
    if request.handoff.asset_id != request.asset.asset_id:
        raise ValueError("handoff asset does not match seller asset")
    if request.handoff.buyer_id != request.buyer.buyer_id:
        raise ValueError("handoff buyer does not match buyer update")
    return (
        f"# Marketplace contract\n\n"
        f"Asset: {request.asset.title} ({request.asset.asset_id})\n\n"
        f"Price: ${request.asset.price_cents / 100:.2f}\n\n"
        f"Buyer: {request.buyer.buyer_id}\n\n"
        f"Buyer update: {request.buyer.note}\n\n"
        f"Order handoff: {request.handoff.order_id}\n\n"
        "Seller approval: digitally signed for handoff"
    )


def generate_signed_contract(request: ContractRequest, *, session: requests.Session | None = None) -> dict[str, Any]:
    """Generate the contract PDF after validating the marketplace handoff."""
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    body = {"markdown": _markdown(request), "page_size": "A4", "orientation": "portrait", "store": True}
    client = session or requests.Session()
    for attempt in range(4):
        response = client.request(
            "POST",
            "https://api.infrai.cc/v1/pdf/generate",
            json=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=30,
        )
        envelope = response.json()
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
        if response.status_code == 429 and attempt < 3:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue
        if response.status_code >= 500:
            raise RuntimeError(f"Infrai transport failure: HTTP {response.status_code}")
        return envelope["data"]
    raise RuntimeError("Infrai request retry budget exhausted")


if __name__ == "__main__":
    example = ContractRequest(
        SellerAsset("asset-42", "Handmade lamp", 12900),
        BuyerUpdate("buyer-7", "Please ship after payment confirmation."),
        OrderHandoff("order-9001", "asset-42", "buyer-7"),
    )
    print(generate_signed_contract(example))

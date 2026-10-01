import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.contract_sign import BuyerUpdate, ContractRequest, OrderHandoff, SellerAsset, _markdown


def test_handoff_must_match_asset_and_buyer():
    request = ContractRequest(
        SellerAsset("asset-1", "Desk", 5000),
        BuyerUpdate("buyer-1", "Ready"),
        OrderHandoff("order-1", "asset-other", "buyer-1"),
    )
    with pytest.raises(ValueError, match="handoff asset"):
        _markdown(request)


def test_contract_markdown_uses_real_line_breaks():
    request = ContractRequest(
        SellerAsset("asset-1", "Desk", 5000),
        BuyerUpdate("buyer-1", "Ready"),
        OrderHandoff("order-1", "asset-1", "buyer-1"),
    )
    markdown = _markdown(request)
    assert markdown.startswith("# Marketplace contract\n\nAsset: Desk (asset-1)\n\n")
    assert "\\n" not in markdown

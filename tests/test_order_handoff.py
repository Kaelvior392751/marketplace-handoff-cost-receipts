from decimal import Decimal

import pytest

from marketplace_handoff.model_brief import BriefResult
from marketplace_handoff.order_handoff import HandoffRequest, RevisionConflict, create_handoff


class RecordingWriter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def write(self, *, order_id: str, prompt: str) -> BriefResult:
        self.calls.append(prompt)
        return BriefResult(
            text="Package revision 3 with captions and export notes.",
            cost_usd=Decimal("0.0042"),
            vendor="example-vendor",
        )


def handoff_request(approved_revision: int) -> HandoffRequest:
    return HandoffRequest.model_validate(
        {
            "order_id": "ord-1042",
            "seller_asset": {
                "asset_id": "video-launch-cut",
                "title": "Launch reel, 30 seconds",
                "revision": 3,
                "production_notes": "Use approved captions.",
            },
            "buyer_update": {
                "buyer_id": "buyer-studio-7",
                "approved_revision": approved_revision,
                "delivery_request": "Include export notes.",
            },
        }
    )


def test_matching_revision_creates_handoff_and_cost_receipt() -> None:
    writer = RecordingWriter()

    result = create_handoff(handoff_request(approved_revision=3), writer)

    assert result.state == "ready_for_production"
    assert result.model_receipt.cost_usd == Decimal("0.0042")
    assert "revision 3" in writer.calls[0]


def test_new_seller_revision_requires_fresh_buyer_approval() -> None:
    writer = RecordingWriter()

    with pytest.raises(RevisionConflict, match="seller asset is revision 3"):
        create_handoff(handoff_request(approved_revision=2), writer)

    assert writer.calls == []

import json

from fastapi.testclient import TestClient

from marketplace_handoff.order_handoff import app


request = {
    "order_id": "ord-1042",
    "seller_asset": {
        "asset_id": "video-launch-cut",
        "title": "Launch reel, 30 seconds",
        "revision": 3,
        "production_notes": "Use the approved captions and deliver a vertical master.",
    },
    "buyer_update": {
        "buyer_id": "buyer-studio-7",
        "approved_revision": 3,
        "delivery_request": "Include the final caption copy and export notes.",
    },
}

response = TestClient(app).post("/orders/handoff", json=request)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))

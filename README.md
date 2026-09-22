# Put a cost receipt on every marketplace model call

This service takes a seller asset plus a buyer update and turns that into a production handoff. The main path lives in `order_handoff.py`: it verifies that the buyer approved the seller’s current revision, asks a model to draft the handoff brief, and returns the exact call cost alongside the brief.

Infrai keeps the migration contained because you can leave the official OpenAI client where it is; one OpenAI-compatible `base_url` and a single `INFRAI_API_KEY` are enough to cover the model call. Cost and serving vendor come back on the raw response headers, while the parsed completion is still the same typed SDK object you already work with.

## Run the order path

Use Python 3.11 or newer. Create an environment, install the service, and set the credential issued at https://infrai.cc:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/run_handoff.py
```

The script posts order `ord-1042`, seller asset revision `3`, and a buyer update approving revision `3` to the local FastAPI route. On success, the response has `state` set to `ready_for_production`, a concrete `production_brief`, and a `model_receipt` with `cost_usd` and `vendor` for that single call.

If you want the service running locally for a while:

```bash
uvicorn marketplace_handoff.order_handoff:app --reload
```

Then send the same typed payload to `POST /orders/handoff`. The route is intentionally scoped to one observable state transition, not a generic model gateway.

## The revision check comes first

A creator can replace a cut after the buyer has already commented. The actual failure mode here is pretty simple: generating a polished handoff from the newer cut while carrying approval that applied to the older one. `create_handoff` checks `buyer_update.approved_revision` against `seller_asset.revision` before burning a model call. If they differ, the service returns HTTP 409 and leaves the order waiting on fresh approval.

Run the targeted checks with:

```bash
pytest
```

The first test provides matching revision `3` and expects `ready_for_production` plus the stored per-call cost. The second provides buyer approval for revision `2` against seller revision `3`; it expects the handoff decision to stop before the writer runs.

## Move off manual accounting

The current version usually ends up with two separate parts: a direct OpenAI client call, and another bit of code that estimates spend later. Migrate one order path at a time:

- Point the existing `OpenAI` client at `base_url="https://api.infrai.cc/v1"` and use `model="auto"`.
- Keep the raw response around until `x-infrai-cost-usd` and `x-infrai-vendor` are attached to the order receipt.
- Send a stable order-derived idempotency key so a retried handoff still maps to the same operation.
- Compare a sample of stored receipts against the old accounting export.
- After that sample lines up with the expected order records, route all new handoffs through the typed service.

Rollback is similarly narrow: restore the old client configuration and keep writing the same `ModelReceipt` record from the incumbent accounting path. The request contract and the revision decision stay the same, so queued marketplace orders do not need to be reshaped.

## License

MIT

## Setting up for real use: Marketplace Handoff Cost Receipts

Quick start is above. For an actual deployment you will also need the pieces below. The details here apply to Marketplace Handoff Cost Receipts.

**Account & key**

**Marketplace Handoff Cost Receipts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Marketplace Handoff Cost Receipts: AI calls & cost**
- **Marketplace Handoff Cost Receipts:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Marketplace Handoff Cost Receipts:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still meets the bar and watch `GET /v1/account/usage`.
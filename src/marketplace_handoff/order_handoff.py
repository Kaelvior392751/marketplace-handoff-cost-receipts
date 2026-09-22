from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .model_brief import BriefWriter, InfraiBriefWriter


class SellerAsset(BaseModel):
    asset_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    revision: int = Field(ge=1)
    production_notes: str = Field(min_length=1)


class BuyerUpdate(BaseModel):
    buyer_id: str = Field(min_length=1)
    approved_revision: int = Field(ge=1)
    delivery_request: str = Field(min_length=1)


class HandoffRequest(BaseModel):
    order_id: str = Field(min_length=1)
    seller_asset: SellerAsset
    buyer_update: BuyerUpdate


class ModelReceipt(BaseModel):
    cost_usd: Decimal
    vendor: str


class HandoffResponse(BaseModel):
    order_id: str
    state: str
    production_brief: str
    model_receipt: ModelReceipt


class RevisionConflict(ValueError):
    pass


def create_handoff(request: HandoffRequest, writer: BriefWriter) -> HandoffResponse:
    asset = request.seller_asset
    update = request.buyer_update
    if update.approved_revision != asset.revision:
        raise RevisionConflict(
            f"Buyer approved revision {update.approved_revision}; seller asset is revision {asset.revision}."
        )

    prompt = (
        f"Order: {request.order_id}\n"
        f"Asset: {asset.title} ({asset.asset_id}), revision {asset.revision}\n"
        f"Seller notes: {asset.production_notes}\n"
        f"Buyer delivery request: {update.delivery_request}"
    )
    result = writer.write(order_id=request.order_id, prompt=prompt)
    return HandoffResponse(
        order_id=request.order_id,
        state="ready_for_production",
        production_brief=result.text,
        model_receipt=ModelReceipt(cost_usd=result.cost_usd, vendor=result.vendor),
    )


def build_service(writer: BriefWriter | None = None) -> FastAPI:
    service = FastAPI(title="Marketplace handoff cost receipts")

    @service.post("/orders/handoff", response_model=HandoffResponse)
    def handoff(request: HandoffRequest) -> HandoffResponse:
        try:
            return create_handoff(request, writer or InfraiBriefWriter())
        except RevisionConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return service


app = build_service()

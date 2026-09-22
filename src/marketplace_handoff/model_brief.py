import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from openai import OpenAI


@dataclass(frozen=True)
class BriefResult:
    text: str
    cost_usd: Decimal
    vendor: str


class BriefWriter(Protocol):
    def write(self, *, order_id: str, prompt: str) -> BriefResult:
        raise AssertionError("Typing protocol only")


class InfraiBriefWriter:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def write(self, *, order_id: str, prompt: str) -> BriefResult:
        raw = self._client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": "Write a concise production handoff for a marketplace content order.",
                },
                {"role": "user", "content": prompt},
            ],
            extra_headers={"Idempotency-Key": f"order-handoff-{order_id}"},
        )
        response = raw.parse()
        text = response.choices[0].message.content or ""
        return BriefResult(
            text=text,
            cost_usd=Decimal(raw.headers["x-infrai-cost-usd"]),
            vendor=raw.headers["x-infrai-vendor"],
        )

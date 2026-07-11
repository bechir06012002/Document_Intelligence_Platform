from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from app.config import settings
from app.pipeline.context import DocumentContext
from app.services.azure_openai_service import MODEL_NAME


class DocumentClassification(BaseModel):
    document_type: Literal["invoice", "receipt"]


def _build_model() -> OpenAIChatModel:
    provider = AzureProvider(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )
    return OpenAIChatModel(MODEL_NAME, provider=provider)


class ClassificationStep:
    def __init__(self) -> None:
        self._agent = Agent(
            _build_model(),
            output_type=DocumentClassification,
            instructions=(
                "Classify the following document text as either an invoice or a receipt. "
                "An invoice bills a customer for goods or services not yet paid. "
                "A receipt confirms a purchase that has already been paid for."
            ),
        )

    def run(self, context: DocumentContext) -> DocumentContext:
        result = self._agent.run_sync(context.text)
        return context.evolve(classification=result.output)

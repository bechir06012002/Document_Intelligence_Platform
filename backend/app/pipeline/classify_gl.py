from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from app.accounting.catalog import GLAccount
from app.config import settings
from app.pipeline.context import DocumentContext
from app.services.azure_openai_service import MODEL_NAME


class GLSuggestion(BaseModel):
    account: GLAccount
    rationale: str


def _build_model() -> OpenAIChatModel:
    provider = AzureProvider(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )
    return OpenAIChatModel(MODEL_NAME, provider=provider)


class GLClassificationStep:
    def __init__(self) -> None:
        self._agent = Agent(
            _build_model(),
            output_type=GLSuggestion,
            instructions=(
                "Suggest the single best-fitting Delta Facilities B.V. general ledger "
                "account for the given invoice or receipt fields, and give a one-sentence "
                "rationale."
            ),
        )

    def run(self, context: DocumentContext) -> DocumentContext:
        fields = context.fields
        prompt = fields.model_dump_json(indent=2) if fields is not None else ""
        result = self._agent.run_sync(prompt)
        return context.evolve(gl_classification=result.output)

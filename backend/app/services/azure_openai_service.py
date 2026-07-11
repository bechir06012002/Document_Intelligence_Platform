from openai import OpenAI

from app.config import settings

MODEL_NAME = settings.azure_openai_deployment


class AzureOpenAIService:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_openai_endpoint,
        )

    def create_response(self, input_text: str) -> str:
        response = self._client.responses.create(model=MODEL_NAME, input=input_text)
        return response.output_text

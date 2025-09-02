import logging

from openai import OpenAI

from svc.app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=settings.openai_base_url,
                api_key=settings.openai_api_key,
                timeout=30.0,
            )
        return self._client


# Singleton instance
llm_client = LLMClient()


import json
import os
from typing import Any, Protocol

import httpx
from dotenv import load_dotenv


GROQ_ENDPOINT = (
    "https://api.groq.com/openai/v1/chat/completions"
)


class LLMUnavailableError(Exception):
    pass


class LLMOutputError(Exception):
    pass


class LLMProvider(Protocol):
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        ...


class GroqProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 45.0,
    ):
        load_dotenv()

        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv("GROQ_API_KEY", "")
        ).strip()

        self.model = (
            model
            or os.getenv(
                "WEBINTEL_RAG_MODEL",
                "openai/gpt-oss-120b",
            )
        )

        self.timeout = timeout

        if not self.api_key:
            raise LLMUnavailableError(
                "Groq API key is not configured"
            )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_completion_tokens": 800,
            "response_format": {
                "type": "json_object",
            },
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:
                response = await client.post(
                    GROQ_ENDPOINT,
                    headers={
                        "Authorization": (
                            f"Bearer {self.api_key}"
                        ),
                        "Content-Type": (
                            "application/json"
                        ),
                    },
                    json=payload,
                )

                response.raise_for_status()

        except (
            httpx.HTTPError,
            httpx.TimeoutException,
        ) as exc:
            # Do not return provider exception strings:
            # they may include request metadata.
            raise LLMUnavailableError(
                "LLM provider request failed"
            ) from exc

        try:
            envelope = response.json()

            content = envelope[
                "choices"
            ][0]["message"]["content"]

            parsed = json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Expected a JSON object"
                )

            return parsed

        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise LLMOutputError(
                "LLM returned an invalid JSON response"
            ) from exc

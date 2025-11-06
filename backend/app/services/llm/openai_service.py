import time
import asyncio
from typing import Dict, List
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from app.services.llm.base import BaseLLMService


class OpenAIService(BaseLLMService):
    """OpenAI GPT service implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize OpenAI service.

        Args:
            api_key: OpenAI API key
            model: Model name to use (gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict:
        """Send a message to OpenAI GPT and get a response.

        Implements retry logic with exponential backoff for transient failures.
        """
        start_time = time.time()

        # Build messages array from history + new message
        messages = [{"role": "system", "content": system_prompt}]

        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "content": response.choices[0].message.content,
                    "tokens_used": response.usage.total_tokens,
                    "model": response.model,
                    "response_time_ms": response_time_ms
                }

            except APITimeoutError:
                if attempt == max_retries - 1:
                    raise Exception("OpenAI API timeout after 3 retries")
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)

            except RateLimitError:
                if attempt == max_retries - 1:
                    raise Exception("OpenAI API rate limit exceeded")
                # Longer backoff for rate limits
                await asyncio.sleep(5 * (attempt + 1))

            except APIError as e:
                # Don't retry on client errors (400-499)
                if e.status_code and 400 <= e.status_code < 500:
                    raise Exception(f"OpenAI API error: {str(e)}")
                # Retry on server errors (500+)
                if attempt == max_retries - 1:
                    raise Exception(f"OpenAI API error after retries: {str(e)}")
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                raise Exception(f"Unexpected error calling OpenAI: {str(e)}")

        raise Exception("OpenAI API: Max retries exceeded")

    async def stream_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """Stream a message response from OpenAI (for Phase 3).

        This is a stub for now - will be implemented in Phase 3.
        """
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        # Stream response
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

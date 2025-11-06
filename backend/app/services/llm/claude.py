import time
import asyncio
from typing import Dict, List
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError
from app.services.llm.base import BaseLLMService


class ClaudeService(BaseLLMService):
    """Claude (Anthropic) LLM service implementation."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Claude service.

        Args:
            api_key: Anthropic API key
            model: Model name to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict:
        """Send a message to Claude and get a response.

        Implements retry logic with exponential backoff for transient failures.
        """
        start_time = time.time()

        # Build messages array from history + new message
        messages = []
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
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages
                )

                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "content": response.content[0].text,
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                    "model": response.model,
                    "response_time_ms": response_time_ms
                }

            except APITimeoutError:
                if attempt == max_retries - 1:
                    raise Exception("Claude API timeout after 3 retries")
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)

            except RateLimitError:
                if attempt == max_retries - 1:
                    raise Exception("Claude API rate limit exceeded")
                # Longer backoff for rate limits
                await asyncio.sleep(5 * (attempt + 1))

            except APIError as e:
                # Don't retry on client errors (400-499)
                if e.status_code and 400 <= e.status_code < 500:
                    raise Exception(f"Claude API error: {str(e)}")
                # Retry on server errors (500+)
                if attempt == max_retries - 1:
                    raise Exception(f"Claude API error after retries: {str(e)}")
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                raise Exception(f"Unexpected error calling Claude: {str(e)}")

        raise Exception("Claude API: Max retries exceeded")

    async def stream_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """Stream a message response from Claude (for Phase 3).

        This is a stub for now - will be implemented in Phase 3.
        """
        # Build messages
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # Stream response
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

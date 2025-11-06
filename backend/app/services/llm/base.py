from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseLLMService(ABC):
    """Abstract base class for LLM service providers."""

    @abstractmethod
    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict:
        """Send a message to the LLM and get a response.

        Args:
            system_prompt: System-level instructions for the LLM
            user_message: The user's message/question
            conversation_history: List of previous messages in format:
                [{"role": "user"|"assistant", "content": "..."}]
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Dictionary containing:
            {
                "content": str,  # The LLM's response text
                "tokens_used": int,  # Total tokens (input + output)
                "model": str,  # Model name used
                "response_time_ms": int  # Response time in milliseconds
            }

        Raises:
            Exception: If the LLM API call fails
        """
        pass

    @abstractmethod
    async def stream_message(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """Stream a message response from the LLM (for Phase 3).

        Args:
            Same as send_message

        Yields:
            str: Chunks of the response as they arrive

        Raises:
            Exception: If the LLM API call fails
        """
        pass

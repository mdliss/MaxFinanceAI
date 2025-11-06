import os
from app.services.llm.base import BaseLLMService


def get_llm_service() -> BaseLLMService:
    """Factory function to get the configured LLM service.

    Returns the appropriate LLM service based on environment configuration.
    Defaults to Claude (Anthropic) as primary provider.

    Returns:
        BaseLLMService: Configured LLM service instance

    Raises:
        ValueError: If required API keys are missing
        ValueError: If configured provider is not supported
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

    if provider == "anthropic" or provider == "claude":
        from app.services.llm.claude import ClaudeService

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your-anthropic-key-here":
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Get your key from https://console.anthropic.com/"
            )

        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        return ClaudeService(api_key=api_key, model=model)

    elif provider == "openai":
        from app.services.llm.openai_service import OpenAIService

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        model = os.getenv("LLM_MODEL", "gpt-4")
        return OpenAIService(api_key=api_key, model=model)

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai"
        )


def get_llm_config() -> dict:
    """Get LLM configuration from environment variables.

    Returns:
        dict: Configuration dictionary with provider, model, max_tokens, temperature
    """
    return {
        "provider": os.getenv("LLM_PROVIDER", "anthropic"),
        "model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7"))
    }

from langchain_anthropic import ChatAnthropic

from appeal_arbiter.config import settings


def get_llm(max_tokens: int = 1024) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        max_tokens=max_tokens,
    )

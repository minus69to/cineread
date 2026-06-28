from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_llm(temperature: float = 0.2) -> BaseChatModel:
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=temperature,
        )

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        max_retries=3,
        default_headers={
            "HTTP-Referer": "https://cineread.app",
            "X-Title": "CineRead",
        },
    )

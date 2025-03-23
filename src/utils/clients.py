from langfuse import Langfuse
from openai import OpenAI

from src.config import settings


def get_openai_client():
    """Return the initialized OpenAI client."""
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return openai_client


def get_langfuse_client():
    """Return the initialized LangFuse client."""
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )
    return langfuse_client

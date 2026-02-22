"""OpenAI API client."""

from typing import AsyncGenerator, List

import openai

from app.core.config import settings
from app.core.exceptions import EmbeddingError, ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configure OpenAI
openai.api_key = settings.openai_api_key


class OpenAIClient:
    """OpenAI API client wrapper."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingError(
                message="Failed to generate embedding",
                details={"error": str(e)},
            )

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingError(
                message="Failed to generate batch embeddings",
                details={"error": str(e)},
            )

    async def chat_completion_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = settings.openai_max_tokens,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        try:
            stream = await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Failed to stream chat completion: {e}")
            raise ExternalServiceError(
                message="Failed to stream chat completion",
                details={"error": str(e)},
            )

    async def chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = settings.openai_max_tokens,
        json_mode: bool = False,
    ) -> str:
        """Generate chat completion (non-streaming)."""
        try:
            kwargs = {
                "model": settings.openai_chat_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Use structured JSON output when requested
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            raise ExternalServiceError(
                message="Failed to generate chat completion",
                details={"error": str(e)},
            )

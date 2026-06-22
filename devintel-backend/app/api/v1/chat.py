"""RAG-powered chat routes — SSE streaming."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.services.chat import ChatService

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatHistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[list[ChatHistoryMessage]] = None


@router.post("/{repository_id}/stream")
async def stream_chat(
    repository_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream an AI chat response for a repository using RAG.

    Returns a Server-Sent Events (SSE) stream.
    Each event is: `data: <json>\n\n`
    where json is one of:
      - `{ "type": "chunk", "content": "..." }`
      - `{ "type": "done" }`
      - `{ "type": "error", "message": "..." }`
    """
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if repository.indexing_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository must be fully indexed before using chat.",
        )

    chat_service = ChatService()
    embedding_repo = EmbeddingRepository(db)

    # Retrieve context chunks (do this before streaming so errors are clean 4xx/5xx)
    try:
        context_chunks = await chat_service.retrieve_relevant_chunks(
            repo_id=repository.id,
            question=request.question,
            embedding_repo=embedding_repo,
        )
    except ValueError as e:
        # Prompt injection detected
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retrieve context chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context from the codebase.",
        )

    history = [msg.model_dump() for msg in request.chat_history] if request.chat_history else []

    async def event_stream():
        try:
            async for chunk in chat_service.stream_chat(
                repo_name=repository.full_name,
                question=request.question,
                context_chunks=context_chunks,
                chat_history=history,
            ):
                payload = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {payload}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except ValueError as e:
            payload = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {payload}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            payload = json.dumps({"type": "error", "message": "An error occurred while generating the response."})
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
            "Connection": "keep-alive",
        },
    )

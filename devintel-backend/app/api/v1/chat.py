"""RAG-powered chat routes — SSE streaming."""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
    repository_id: uuid.UUID,
    request: ChatRequest,
    http_request: Request,
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

    if repository.indexing_status not in ("completed", "complete"):
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
    request_id = getattr(http_request.state, "request_id", None) or "unknown"

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

        except Exception as e:
            logger.error(
                "Chat stream error [request_id=%s]: %s",
                request_id,
                e,
                exc_info=True,
            )
            error_payload = {
                "type": "error",
                "message": "An error occurred while processing your request.",
            }
            if request_id and request_id != "unknown":
                error_payload["request_id"] = request_id
            payload = json.dumps(error_payload)
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


from app.core.security import decrypt_token
from app.schemas.chat import (
    AgentDraftRequest,
    AgentDraftResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentExecuteWithTestsResponse,
)
from app.services.agent import AgentService


@router.post("/draft", response_model=AgentDraftResponse)
async def agent_draft(
    request: AgentDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a draft PR proposal for user review."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    if not current_user.github_token_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token not found. Please re-authenticate.")

    if repository.indexing_status != "complete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository must be indexed.")

    token = decrypt_token(current_user.github_token_encrypted)
    agent_service = AgentService(token)
    embedding_repo = EmbeddingRepository(db)

    try:
        draft_payload = await agent_service.draft_pr_plan(
            repository=repository,
            instruction=request.instruction,
            embedding_repo=embedding_repo,
        )
        return AgentDraftResponse(draft=draft_payload)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to generate agent draft: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while drafting the PR.")


@router.post("/execute", response_model=AgentExecuteResponse | AgentExecuteWithTestsResponse)
async def agent_execute(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved draft PR on GitHub. Optionally generates tests first."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    if not current_user.github_token_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token not found. Please re-authenticate.")

    token = decrypt_token(current_user.github_token_encrypted)
    agent_service = AgentService(token)

    try:
        draft_dict = request.draft.model_dump()
        result = await agent_service.execute_pr(
            repository=repository,
            draft_payload=draft_dict,
            default_branch=repository.default_branch
        )

        if result.get("status") == "tests_failed":
            return AgentExecuteWithTestsResponse(**result)

        return AgentExecuteResponse(**result)
    except Exception as e:
        logger.error(f"Failed to execute agent PR: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while executing the PR on GitHub.")

"""Chat routes with RAG."""

import asyncio
import json
import time
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, check_repo_access
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository
from app.repositories.chat import ChatRepository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.chat import (
    AgentDraftRequest,
    AgentDraftResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
    ChatHistoryRecord,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.agent import AgentService
from app.services.chat import ChatService
from app.services.encryption import encryption_service
from app.services.organization_service import OrganizationService

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/history/{repository_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chat history for a repository."""
    # Check repo access
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    chat_repo = ChatRepository(db)
    chats = await chat_repo.get_by_user_and_repo(
        user_id=current_user.id,
        repo_id=repository_id,
        org_id=repository.org_id,
        limit=50,
    )

    # Convert to messages (two messages per chat record)
    messages = []
    # Reverse to get chronological order (repo returns desc)
    for chat in reversed(chats):
        messages.append(
            ChatHistoryRecord(
                role="user",
                content=chat.question,
                timestamp=chat.created_at,
            )
        )
        messages.append(
            ChatHistoryRecord(
                role="assistant",
                content=chat.response,
                timestamp=chat.created_at,
            )
        )

    return ChatHistoryResponse(messages=messages, repository_id=repository_id)


async def stream_chat_response(
    chat_request: ChatRequest,
    current_user: User,
) -> AsyncGenerator[str, None]:
    """Stream chat response as Server-Sent Events."""
    from app.db.session import AsyncSessionLocal
    
    try:
        # Pre-load data in a short-lived session
        async with AsyncSessionLocal() as db:
            # Get repository
            repo_repo = RepositoryRepository(db)
            repository = await repo_repo.get_by_id(chat_request.repository_id)
            
            if not repository:
                yield f"data: {json.dumps({'error': 'Repository not found'})}\n\n"
                return

            # Authorization check
            try:
                await check_repo_access(repository, current_user, db)
            except Exception:
                yield f"data: {json.dumps({'error': 'Not authorized'})}\n\n"
                return
            
            if not repository.indexed_status:
                yield f"data: {json.dumps({'error': 'Repository not indexed yet'})}\n\n"
                return
            
            # Retrieve relevant chunks
            chat_service = ChatService()
            embedding_repo = EmbeddingRepository(db)
            
            context_chunks = await chat_service.retrieve_relevant_chunks(
                repo_id=chat_request.repository_id,
                question=chat_request.question,
                embedding_repo=embedding_repo,
            )
            repo_full_name = repository.full_name
            # db session closes here
        
        # Track response time
        start_time = time.time()
        
        # Stream response
        full_response = ""
        async for chunk in chat_service.stream_chat(
            repo_name=repo_full_name,
            question=chat_request.question,
            context_chunks=context_chunks,
            chat_history=chat_request.chat_history,
        ):
            full_response += chunk
            # Send SSE chunk
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        
        # Calculate real token usage
        response_time_ms = int((time.time() - start_time) * 1000)
        input_tokens = chat_service.count_tokens(chat_request.question)
        output_tokens = chat_service.count_tokens(full_response)
        total_tokens = input_tokens + output_tokens

        # Calculate cost (GPT-4o pricing: $2.50/1M input tokens, $10.00/1M output tokens)
        cost_usd = (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.00 / 1_000_000)

        # Save chat history in another short-lived session
        async with AsyncSessionLocal() as db:
            chat_repo = ChatRepository(db)
            chat = await chat_repo.create(
                user_id=current_user.id,
                repo_id=chat_request.repository_id,
                org_id=repository.org_id,
                question=chat_request.question,
                response=full_response,
                token_usage=total_tokens,
                response_time_ms=response_time_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )

            # Update analytics with real token count
            analytics_repo = AnalyticsRepository(db)
            await analytics_repo.increment_query_count(current_user.id, tokens=total_tokens)

            await db.commit()
            chat_id_str = str(chat.id)
            # db session closes here

        # Send final chunk with token info and cost
        yield f"data: {json.dumps({'content': '', 'done': True, 'chat_id': chat_id_str, 'token_usage': total_tokens, 'input_tokens': input_tokens, 'output_tokens': output_tokens, 'cost_usd': round(cost_usd, 8), 'response_time_ms': response_time_ms})}\n\n"
        
    except Exception as e:
        logger.error(f"Chat streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': 'An internal error occurred. Please try again.'})}\n\n"


@router.post("")
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Chat with repository using RAG (streaming)."""
    return StreamingResponse(
        stream_chat_response(chat_request, current_user),
        media_type="text/event-stream",
    )


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
        
    if not current_user.github_access_token_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token not found. Please re-authenticate.")
        
    if not repository.indexed_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository must be indexed.")

    token = encryption_service.decrypt(current_user.github_access_token_encrypted)
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
        logger.error(f"Failed to generate agent draft: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while drafting the PR.")


@router.post("/execute", response_model=AgentExecuteResponse)
async def agent_execute(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved draft PR on GitHub."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)
    
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)
        
    if not current_user.github_access_token_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token not found. Please re-authenticate.")

    token = encryption_service.decrypt(current_user.github_access_token_encrypted)
    agent_service = AgentService(token)
    
    try:
        # Convert DraftPayload schema to dict for service method
        draft_dict = request.draft.model_dump()
        result = await agent_service.execute_pr(
            repository=repository,
            draft_payload=draft_dict,
            default_branch=repository.default_branch
        )
        return AgentExecuteResponse(**result)
    except Exception as e:
        logger.error(f"Failed to execute agent PR: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while executing the PR on GitHub.")

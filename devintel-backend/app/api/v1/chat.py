"""Chat routes with RAG."""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository
from app.repositories.chat import ChatRepository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


async def stream_chat_response(
    chat_request: ChatRequest,
    current_user: User,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Stream chat response as Server-Sent Events."""
    try:
        # Get repository
        repo_repo = RepositoryRepository(db)
        repository = await repo_repo.get_by_id(chat_request.repository_id)
        
        if not repository:
            yield f"data: {json.dumps({'error': 'Repository not found'})}\n\n"
            return
        
        if repository.user_id != current_user.id:
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
        
        # Stream response
        full_response = ""
        async for chunk in chat_service.stream_chat(
            repo_name=repository.full_name,
            question=chat_request.question,
            context_chunks=context_chunks,
        ):
            full_response += chunk
            # Send SSE chunk
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        
        # Save chat history
        chat_repo = ChatRepository(db)
        chat = await chat_repo.create(
            user_id=current_user.id,
            repo_id=chat_request.repository_id,
            question=chat_request.question,
            response=full_response,
            token_usage=0,  # Calculate in production
        )
        
        # Update analytics
        analytics_repo = AnalyticsRepository(db)
        await analytics_repo.increment_query_count(current_user.id, tokens=0)
        
        await db.commit()
        
        # Send final chunk
        yield f"data: {json.dumps({'content': '', 'done': True, 'chat_id': str(chat.id)})}\n\n"
        
    except Exception as e:
        logger.error(f"Chat streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.post("")
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with repository using RAG (streaming)."""
    return StreamingResponse(
        stream_chat_response(chat_request, current_user, db),
        media_type="text/event-stream",
    )

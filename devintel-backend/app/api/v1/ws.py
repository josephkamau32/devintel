"""WebSocket endpoint for real-time repository indexing progress.

Uses the in-process ProgressBus instead of Redis pub/sub.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.collaboration import CollaborationSessionRepository
from app.repositories.repository import RepositoryRepository
from app.repositories.user import UserRepository
from app.services.collaboration_service import CollaborationService
from app.services.progress_bus import progress_bus

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/repos/{repo_id}/progress")
async def repo_indexing_progress(
    websocket: WebSocket,
    repo_id: str,
):
    """
    WebSocket endpoint for real-time indexing progress updates.

    Clients connect with a JWT token in the query string:
        ws://host/ws/repos/{repo_id}/progress?token=<jwt>

    The server:
    1. Validates the JWT and checks repo access
    2. Subscribes to the in-process progress bus channel `indexing:{repo_id}`
    3. Forwards every progress message to the WebSocket client
    4. Disconnects when progress reaches 100 or on error

    Message format (JSON):
        { "progress": 0-100, "status": "cloning" | "parsing" | "embedding" | "completing" | "done" | "error" }
    """
    # 1. Authenticate via query param token
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("No subject")
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Accept the connection
    await websocket.accept()

    # 3. Verify repo access
    try:
        repo_uuid = UUID(repo_id)
        async with AsyncSessionLocal() as db:
            repo_repo = RepositoryRepository(db)
            repository = await repo_repo.get_by_id(repo_uuid)
            if not repository:
                await websocket.send_json({"error": "Repository not found"})
                await websocket.close()
                return

            # Check ownership (user_id match or org membership check skipped for WS simplicity)
            if repository.user_id and str(repository.user_id) != user_id:
                await websocket.send_json({"error": "Not authorized"})
                await websocket.close()
                return

            # If already indexed, send 100 immediately
            if repository.indexed_status and repository.indexing_progress == 100:
                await websocket.send_json({"progress": 100, "status": "done"})
                await websocket.close()
                return

            current_progress = repository.indexing_progress
    except Exception as e:
        logger.error(f"WS repo lookup failed: {e}")
        await websocket.send_json({"error": "Internal error"})
        await websocket.close()
        return

    # 4. Send current progress immediately so the UI can bootstrap
    await websocket.send_json({"progress": current_progress, "status": "connecting"})

    # 5. Subscribe to in-process progress bus and stream events
    channel = f"indexing:{repo_id}"

    try:
        logger.info(f"WebSocket client subscribed to {channel}")

        async for data in progress_bus.subscribe(channel):
            try:
                await websocket.send_json(data)

                # Close once indexing is terminal
                progress = data.get("progress", 0)
                msg_status = data.get("status", "")
                if progress >= 100 or msg_status in ("done", "error"):
                    break
            except WebSocketDisconnect:
                logger.info(f"WS client disconnected from {channel}")
                break
            except Exception as e:
                logger.warning(f"Error forwarding WS message: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WS client disconnected from {channel}")
    except Exception as e:
        logger.error(f"WebSocket error for {channel}: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/collab/{session_id}")
async def collaboration_ws(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time collaboration.

    Clients connect with a JWT token in the query string:
        ws://host/ws/collab/{session_id}?token=<jwt>

    Message types:
        - text: Chat message
        - cursor: Cursor position update
        - code_change: Code edit
        - ai_suggestion: AI-generated suggestion
    """
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("No subject")
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    request_id = websocket.headers.get("x-request-id") or getattr(getattr(websocket, "state", None), "request_id", None)
    try:
        session_uuid = UUID(session_id)
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        async with AsyncSessionLocal() as db:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(user_uuid)

            if not user:
                await websocket.send_json({"error": "User not found"})
                await websocket.close()
                return

            session_repo = CollaborationSessionRepository(db)
            session = await session_repo.get_by_id(session_uuid)

            if not session or not session.is_active:
                await websocket.send_json({"error": "Session not found or inactive"})
                await websocket.close()
                return

            collab_service = CollaborationService(db)

            # Send connection confirmation
            await websocket.send_json({
                "type": "connected",
                "session_id": str(session.id),
                "user": {"id": str(user.id), "login": user.github_login} if user.github_login else {"id": str(user.id)},
            })

            # Handle incoming messages
            async for message in websocket.iter_json():
                msg_type = message.get("type", "text")
                content = message.get("content", "")

                # Store and broadcast message
                await collab_service.add_message(
                    session=session,
                    user=user,
                    message_type=msg_type,
                    content=content,
                    file_path=message.get("file_path"),
                    cursor_line=message.get("cursor_line"),
                    cursor_column=message.get("cursor_column"),
                )

                # Acknowledge to sender
                await websocket.send_json({
                    "type": "ack",
                    "message_type": msg_type,
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except Exception as e:
        if request_id:
            logger.error("Collaboration WS error [request_id=%s]: %s", request_id, e, exc_info=True)
            err_payload = {"error": "An error occurred while processing your request.", "request_id": request_id}
        else:
            logger.error("Collaboration WS error: %s", e, exc_info=True)
            err_payload = {"error": "An error occurred while processing your request."}
        try:
            await websocket.send_json(err_payload)
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

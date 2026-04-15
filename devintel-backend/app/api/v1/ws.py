"""WebSocket endpoint for real-time repository indexing progress.

Uses the in-process ProgressBus instead of Redis pub/sub.
"""

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.repository import RepositoryRepository
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
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
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

"""Tests for GitHub webhook handler and signature verification (F-01 security fix)."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.webhook import verify_github_signature
from app.models.repository import Repository
from app.models.user import User


def _compute_sig(payload: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


# ── Unit tests for verify_github_signature ────────────────────────────


def test_verify_signature_missing_header():
    assert verify_github_signature(b'{"test": 1}', None, secret="test-secret") is False
    assert verify_github_signature(b'{"test": 1}', "", secret="test-secret") is False


def test_verify_signature_invalid_format():
    assert (
        verify_github_signature(
            b'{"test": 1}', "invalid_sig", secret="test-secret"
        )
        is False
    )


def test_verify_signature_mismatch():
    sig = _compute_sig(b'{"test": 1}', "test-secret")
    assert (
        verify_github_signature(
            b'{"test": 2}', sig, secret="test-secret"
        )
        is False
    )


def test_verify_signature_valid():
    payload = b'{"action": "ping"}'
    sig = _compute_sig(payload, "test-secret")
    assert verify_github_signature(payload, sig, secret="test-secret") is True


def test_verify_signature_unset_secret_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", "")
    with pytest.raises(RuntimeError, match="GITHUB_WEBHOOK_SECRET is not configured"):
        verify_github_signature(b'{"test": 1}', "sha256=12345", secret=None)


# ── Endpoint tests for /api/v1/webhooks/github ─────────────────────────


@pytest.mark.asyncio
async def test_missing_signature_header_returns_401(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", "test-secret")
    response = await client.post(
        "/api/v1/webhooks/github",
        json={"zen": "Non-blocking is better than blocking."},
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv-1",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


@pytest.mark.asyncio
async def test_invalid_signature_returns_401(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", "test-secret")
    response = await client.post(
        "/api/v1/webhooks/github",
        json={"zen": "Non-blocking is better than blocking."},
        headers={
            "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv-2",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


@pytest.mark.asyncio
async def test_missing_delivery_header_returns_401(client: AsyncClient, monkeypatch):
    secret = "test-secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)
    payload = json.dumps({"zen": "hello"}).encode("utf-8")
    sig = _compute_sig(payload, secret)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "ping",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-GitHub-Delivery header."


@pytest.mark.asyncio
async def test_webhook_secret_unset_rejects_requests(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", "")
    payload = json.dumps({"zen": "hello"}).encode("utf-8")
    sig = _compute_sig(payload, "any-secret")

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv-unset",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature."


@pytest.mark.asyncio
async def test_valid_signature_first_delivery_triggers_task(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    monkeypatch,
):
    secret = "test-secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    repo = Repository(
        user_id=test_user.id,
        repo_name="webhook-repo",
        full_name="org/webhook-repo",
        description="Webhook test repo",
        url="https://github.com/org/webhook-repo",
        default_branch="main",
    )
    db_session.add(repo)
    await db_session.commit()

    payload_data = {
        "repository": {
            "full_name": "org/webhook-repo",
            "default_branch": "main",
        },
        "ref": "refs/heads/main",
        "after": "c0ffee123456",
        "commits": [],
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = _compute_sig(payload_bytes, secret)
    delivery_id = "deliv-push-unique-01"

    with patch("app.api.v1.webhooks.index_repository_task", new_callable=AsyncMock) as mock_index:
        response = await client.post(
            "/api/v1/webhooks/github",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": delivery_id,
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert data["repository"] == "org/webhook-repo"
        assert mock_index.call_count == 1


@pytest.mark.asyncio
async def test_valid_signature_replay_delivery_returns_202_without_retriggering_task(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    monkeypatch,
):
    secret = "test-secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    repo = Repository(
        user_id=test_user.id,
        repo_name="replay-repo",
        full_name="org/replay-repo",
        description="Replay test repo",
        url="https://github.com/org/replay-repo",
        default_branch="main",
    )
    db_session.add(repo)
    await db_session.commit()

    payload_data = {
        "repository": {
            "full_name": "org/replay-repo",
            "default_branch": "main",
        },
        "ref": "refs/heads/main",
        "after": "deadbeef9999",
        "commits": [],
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = _compute_sig(payload_bytes, secret)
    delivery_id = "deliv-push-replay-02"

    with patch("app.api.v1.webhooks.index_repository_task", new_callable=AsyncMock) as mock_index:
        # First delivery
        res1 = await client.post(
            "/api/v1/webhooks/github",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": delivery_id,
            },
        )
        assert res1.status_code == 202
        assert res1.json()["status"] == "queued"
        assert mock_index.call_count == 1

        # Second delivery (replay with same delivery ID)
        res2 = await client.post(
            "/api/v1/webhooks/github",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": delivery_id,
            },
        )
        assert res2.status_code == 202
        assert res2.json()["status"] == "ignored"
        assert res2.json()["reason"] == "Duplicate delivery ID"
        # Verify task was NOT called again (called exactly once total)
        assert mock_index.call_count == 1


@pytest.mark.asyncio
async def test_ping_event_with_valid_signature_returns_pong(
    client: AsyncClient,
    monkeypatch,
):
    secret = "test-secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    payload_data = {"zen": "Mind your words, they become actions."}
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = _compute_sig(payload_bytes, secret)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv-ping-01",
        },
    )
    assert response.status_code == 202
    assert response.json() == {"status": "pong", "message": "Webhook registered successfully."}



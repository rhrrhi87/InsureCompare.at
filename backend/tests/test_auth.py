"""Authentication endpoint tests.

File: backend/tests/test_auth.py
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@test.at",
            "password": "secret123",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@test.at"
    assert body["role"] == "user"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "user@test.at", "password": "user123"}
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_with_seeded_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"email": "user@test.at", "password": "user123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_bad_password_returns_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"email": "user@test.at", "password": "WRONG"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_returns_current_user(client: AsyncClient) -> None:
    login = await client.post(
        "/api/auth/login",
        json={"email": "user@test.at", "password": "user123"},
    )
    token = login.json()["access_token"]
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.at"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_and_invalidates_old_token(client: AsyncClient) -> None:
    login = await client.post(
        "/api/auth/login",
        json={"email": "user@test.at", "password": "user123"},
    )
    original_refresh = login.json()["refresh_token"]

    refreshed = await client.post(
        "/api/auth/refresh", json={"refresh_token": original_refresh}
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != original_refresh

    # The original refresh token was single-use: reusing it must now fail
    # even though its JWT signature and expiry are still technically valid.
    reused = await client.post(
        "/api/auth/refresh", json={"refresh_token": original_refresh}
    )
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_the_refresh_token(client: AsyncClient) -> None:
    login = await client.post(
        "/api/auth/login",
        json={"email": "user@test.at", "password": "user123"},
    )
    refresh_token = login.json()["refresh_token"]

    logout = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    after_logout = await client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert after_logout.status_code == 401

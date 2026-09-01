"""Integration tests for the recommendation endpoint.

File: backend/tests/test_recommendation_api.py
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, pw: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": pw})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_recommend_returns_ranked_policies(client: AsyncClient) -> None:
    token = await _login(client, "user@test.at", "user123")
    resp = await client.post(
        "/api/recommend",
        headers={"Authorization": f"Bearer {token}"},
        json={"top_k": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["product_line"] == "car"
    assert len(body["ranked_policies"]) >= 1
    assert body["counterfactual"] is not None
    # Scores should be in descending order
    scores = [p["score"] for p in body["ranked_policies"]]
    assert scores == sorted(scores, reverse=True)
    # Each policy must have a non-empty contributions list
    for sp in body["ranked_policies"]:
        assert sp["contributions"]
        assert all("contribution" in c for c in sp["contributions"])


@pytest.mark.asyncio
async def test_recommend_unauthenticated_is_401(client: AsyncClient) -> None:
    resp = await client.post("/api/recommend", json={})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_compare_endpoint(client: AsyncClient) -> None:
    token = await _login(client, "user@test.at", "user123")

    # Discover policy IDs
    resp = await client.get(
        "/api/policies",
        headers={"Authorization": f"Bearer {token}"},
        params={"product_line": "car"},
    )
    ids = [p["id"] for p in resp.json()][:2]
    assert len(ids) == 2

    cmp = await client.post(
        "/api/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={"policy_ids": ids},
    )
    assert cmp.status_code == 200
    summary = cmp.json()["summary"]
    assert summary["cheapest_monthly_eur"] > 0


@pytest.mark.asyncio
async def test_admin_stats_requires_admin(client: AsyncClient) -> None:
    user_token = await _login(client, "user@test.at", "user123")
    forbidden = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert forbidden.status_code == 403

    admin_token = await _login(client, "admin@insurance.at", "admin123")
    ok = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["total_users"] >= 2
    assert body["total_policies"] >= 2

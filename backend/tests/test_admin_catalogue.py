"""Integration tests for admin provider/policy management and audit logging.

File: backend/tests/test_admin_catalogue.py
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, pw: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": pw})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _admin_token(client: AsyncClient) -> str:
    return await _login(client, "admin@insurance.at", "admin123")


@pytest.mark.asyncio
async def test_retire_policy_hides_it_from_default_listing(client: AsyncClient) -> None:
    admin_token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    listed = await client.get("/api/policies", headers=headers, params={"product_line": "car"})
    policy_id = listed.json()[0]["id"]

    retired = await client.post(f"/api/policies/{policy_id}/retire", headers=headers)
    assert retired.status_code == 200
    assert retired.json()["is_active"] is False
    assert retired.json()["retired_at"] is not None

    active_only = await client.get(
        "/api/policies", headers=headers, params={"product_line": "car"}
    )
    assert all(p["id"] != policy_id for p in active_only.json())

    including_retired = await client.get(
        "/api/policies",
        headers=headers,
        params={"product_line": "car", "active_only": False},
    )
    assert any(p["id"] == policy_id for p in including_retired.json())

    reactivated = await client.post(f"/api/policies/{policy_id}/reactivate", headers=headers)
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True
    assert reactivated.json()["retired_at"] is None


@pytest.mark.asyncio
async def test_retire_requires_admin(client: AsyncClient) -> None:
    user_token = await _login(client, "user@test.at", "user123")
    listed = await client.get(
        "/api/policies",
        headers={"Authorization": f"Bearer {user_token}"},
        params={"product_line": "car"},
    )
    policy_id = listed.json()[0]["id"]

    forbidden = await client.post(
        f"/api/policies/{policy_id}/retire",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_policy_clauses_endpoint_empty_for_demo_catalogue(client: AsyncClient) -> None:
    """Seed catalogue policies have no attached source document, so the
    evidence endpoint must honestly report an empty list rather than
    fabricating clause text."""
    admin_token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    listed = await client.get("/api/policies", headers=headers, params={"product_line": "car"})
    policy_id = listed.json()[0]["id"]

    resp = await client.get(f"/api/policies/{policy_id}/clauses", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_policy_create_and_retire_are_audited(client: AsyncClient) -> None:
    admin_token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    providers = await client.get("/api/providers", headers=headers)
    provider_id = providers.json()[0]["id"]

    created = await client.post(
        "/api/policies",
        headers=headers,
        json={
            "provider_id": provider_id,
            "name": "Test Audit Policy",
            "product_line": "car",
            "monthly_premium_eur": 50.0,
            "annual_premium_eur": 600.0,
            "deductible_eur": 300.0,
            "coverage_limit_eur": 1_000_000.0,
        },
    )
    assert created.status_code == 201
    policy_id = created.json()["id"]

    await client.post(f"/api/policies/{policy_id}/retire", headers=headers)

    audit = await client.get("/api/admin/audit", headers=headers, params={"limit": 500})
    actions = {(row["action"], row["entity_id"]) for row in audit.json()}
    assert ("POLICY_CREATED", policy_id) in actions
    assert ("POLICY_RETIRED", policy_id) in actions


@pytest.mark.asyncio
async def test_login_and_recommendation_are_audited(client: AsyncClient) -> None:
    admin_token = await _admin_token(client)
    user_token = await _login(client, "user@test.at", "user123")

    await client.post(
        "/api/recommend",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"top_k": 3},
    )

    audit = await client.get(
        "/api/admin/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"limit": 500},
    )
    actions = [row["action"] for row in audit.json()]
    assert "LOGIN" in actions
    assert "RECOMMENDATION_GENERATED" in actions


@pytest.mark.asyncio
async def test_changing_scoring_weights_is_audited(client: AsyncClient) -> None:
    admin_token = await _admin_token(client)
    user_token = await _login(client, "user@test.at", "user123")
    headers = {"Authorization": f"Bearer {user_token}"}

    profile = await client.get("/api/profiles/me", headers=headers)
    body = profile.json()
    body["weights"] = {
        "price": 0.4, "coverage": 0.2, "exclusion": 0.2, "deductible": 0.1, "fit": 0.1,
    }
    updated = await client.put("/api/profiles/me", headers=headers, json=body)
    assert updated.status_code == 200

    audit = await client.get(
        "/api/admin/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"limit": 500},
    )
    actions = [row["action"] for row in audit.json()]
    assert "WEIGHTS_CHANGED" in actions

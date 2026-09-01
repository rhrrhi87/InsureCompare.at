"""Seed script for development and demo environments.

File: backend/scripts/seed.py

Run with::

    python -m scripts.seed

Idempotent: re-running will not duplicate providers / policies / users.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    ProductLine,
    RiskLevel,
    RiskTolerance,
    UserRole,
)
from app.db.models import Policy, Provider, RiskProfile, User
from app.db.session import AsyncSessionLocal

logger = get_logger("seed")


# ---------------------------------------------------------------------------
# Catalogue data
# ---------------------------------------------------------------------------
# Real Austrian insurers, used here only as catalogue labels (see
# docs/DATA_SOURCES.md — "Seeded provider catalogue"). Every logo_url points
# at that insurer's own public website (verified reachable on 2026-08-28);
# see docs/DATA_PROVENANCE_AUDIT.md for the full source table (source page,
# retrieval date, confidence). rating_score is intentionally the same
# uniform placeholder (8.0 = the Provider model default) for every entry:
# InsureCompare.at has no real, sourced rating methodology, and assigning
# different-looking numbers per insurer would misrepresent placeholder data
# as a genuine rating. Do not differentiate this value without a real,
# documented rating source.
PROVIDERS: list[dict] = [
    {
        "name": "UNIQA Österreich Versicherungen AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://a.storyblok.com/f/172351/184x33/c5c80da7aa/uniqa-logo.svg",
    },
    {
        "name": "Allianz Elementar Versicherungs-AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.allianz.at/content/dam/onemarketing/system/allianz-logo.svg",
    },
    {
        "name": "WIENER STÄDTISCHE Versicherung AG – Vienna Insurance Group",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.wienerstaedtische.at/_assets/ce68916e315ee1d4adb38520616d3214/img/wstv_logo.svg",
    },
    {
        "name": "Generali Versicherung AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.generali.at/static/lg_generali_horizonal_red-c0cb099b6d0f4b6ff97a7ca024eecc79.svg",
    },
    {
        "name": "DONAU Versicherung AG – Vienna Insurance Group",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.donauversicherung.at/_assets/5266fe412c2d21acb7b1cd0fac12c7b4/Images/donau-logo.svg",
    },
    {
        "name": "Zürich Versicherungs-AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.zurich.at/-/media-assets/project/zurich-headless/shared/corporate/zurich-logo-blue.svg",
    },
    {
        "name": "Grazer Wechselseitige Versicherung AG (GRAWE)",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.grawe.at/_assets/4cea41de5990adfadd9564ae0ec315e0/Images/grawe-logo.svg",
    },
    {
        "name": "Helvetia Versicherungen AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.helvetia.com/content/dam/os/at/transport/layout/logo/helvetia-logo-color-pos-170px.svg",
    },
    {
        "name": "ERGO Versicherung AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://ergo-versicherung.at/_assets/5e439985603ece5f8b37fa61dd03305a/Logos/ergo-logo-claim.svg",
    },
    {
        "name": "VAV Versicherungs-AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.vav.at/dam/jcr:4dc812f4-a21d-41ab-8b55-0b4fb16e77ad/VAV-LOGO_CMYK.png",
    },
    {
        "name": "Wüstenrot Versicherungs-AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.wuestenrot.at/content/dam/wuestenrot-aem/home/LogoDesktop.svg",
    },
    {
        "name": "TIROLER VERSICHERUNG V.a.G.",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.tiroler-versicherung.at/extension/tiroler_at_responsive/design/tiroler_at_redesign_2017/images/tiroler_neu.svg",
    },
    {
        "name": "Niederösterreichische Versicherung AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.nv.at/nv/logos/nv-logos/nv_logo_2022_hoch_rgb.png",
    },
    {
        "name": "OBERÖSTERREICHISCHE Versicherung AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.versich.at/build/images/logo/logo-double-line.svg",
    },
    {
        "name": "Europäische Reiseversicherung AG",
        "country": "AT", "rating_score": 8.0,
        "logo_url": "https://www.europaeische.at/typo3conf/ext/erv_site_package/Resources/Public/Images/erv_logo_L.png",
    },
]

# Legacy short names used by the original 6-provider demo catalogue below,
# mapped onto the real legal names above so existing POLICIES entries keep
# referential integrity without inventing any new products.
_LEGACY_PROVIDER_ALIAS: dict[str, str] = {
    "UNIQA": "UNIQA Österreich Versicherungen AG",
    "Allianz Austria": "Allianz Elementar Versicherungs-AG",
    "Wiener Städtische": "WIENER STÄDTISCHE Versicherung AG – Vienna Insurance Group",
    "Generali Austria": "Generali Versicherung AG",
    "Donau Versicherung": "DONAU Versicherung AG – Vienna Insurance Group",
    "Helvetia Austria": "Helvetia Versicherungen AG",
}

POLICIES: list[dict] = [
    # ---- Car (Kfz) ----
    {
        "provider": "UNIQA",
        "name": "UNIQA Kfz Premium",
        "product_line": ProductLine.CAR,
        "monthly_premium_eur": 70.0, "annual_premium_eur": 840.0,
        "deductible_eur": 500.0, "coverage_limit_eur": 100_000_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Liability coverage", "Comprehensive coverage", "Collision coverage",
            "Glass breakage", "Theft protection",
        ],
        "additional_features": [
            "24/7 Roadside assistance", "Replacement vehicle", "Europe-wide coverage",
        ],
        "exclusions": ["Racing events", "Intentional damage"],
        "description": "Premium motor cover with comprehensive protection.",
    },
    {
        "provider": "Allianz Austria",
        "name": "Allianz Auto Komplett",
        "product_line": ProductLine.CAR,
        "monthly_premium_eur": 76.67, "annual_premium_eur": 920.0,
        "deductible_eur": 300.0, "coverage_limit_eur": 150_000_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Liability coverage", "Comprehensive coverage", "Collision coverage",
            "Glass breakage", "Theft protection", "Personal accident",
        ],
        "additional_features": ["Roadside assistance", "EU coverage"],
        "exclusions": ["Racing events", "Gross negligence"],
        "description": "Top-tier motor protection from Allianz Austria.",
    },
    {
        "provider": "Wiener Städtische",
        "name": "WS Auto Basic",
        "product_line": ProductLine.CAR,
        "monthly_premium_eur": 54.17, "annual_premium_eur": 650.0,
        "deductible_eur": 800.0, "coverage_limit_eur": 50_000_000.0,
        "risk_level": RiskLevel.MEDIUM,
        "coverage_items": ["Liability coverage", "Glass breakage", "Theft protection"],
        "additional_features": ["Basic roadside support"],
        "exclusions": ["Racing events", "Comprehensive damage"],
        "description": "Budget motor liability cover for low-risk drivers.",
    },

    # ---- Household ----
    {
        "provider": "UNIQA",
        "name": "Home Protect Plus",
        "product_line": ProductLine.HOUSEHOLD,
        "monthly_premium_eur": 28.33, "annual_premium_eur": 340.0,
        "deductible_eur": 150.0, "coverage_limit_eur": 250_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Fire damage", "Storm damage", "Water damage",
            "Theft protection", "Bicycle theft", "Home electronics",
        ],
        "additional_features": ["Glass insurance", "Garden coverage"],
        "exclusions": ["Gross negligence", "War / civil unrest"],
        "description": "Comprehensive household contents protection.",
    },
    {
        "provider": "Allianz Austria",
        "name": "Smart Home Cover",
        "product_line": ProductLine.HOUSEHOLD,
        "monthly_premium_eur": 30.42, "annual_premium_eur": 365.0,
        "deductible_eur": 100.0, "coverage_limit_eur": 300_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Fire damage", "Storm damage", "Water damage",
            "Theft protection", "Bicycle theft", "Smart device coverage",
        ],
        "additional_features": ["Smart leak sensors", "App-based claims"],
        "exclusions": ["Intentional damage"],
        "description": "Modern household policy with smart-home coverage.",
    },
    {
        "provider": "Wiener Städtische",
        "name": "Wohnen Aktiv",
        "product_line": ProductLine.HOUSEHOLD,
        "monthly_premium_eur": 29.58, "annual_premium_eur": 355.0,
        "deductible_eur": 200.0, "coverage_limit_eur": 200_000.0,
        "risk_level": RiskLevel.MEDIUM,
        "coverage_items": ["Fire damage", "Water damage", "Theft protection", "Storm damage"],
        "additional_features": ["Liability rider"],
        "exclusions": ["Gross negligence"],
        "description": "Reliable Austrian household cover with a flexible deductible.",
    },

    # ---- Travel ----
    {
        "provider": "Helvetia Austria",
        "name": "Travel Secure",
        "product_line": ProductLine.TRAVEL,
        "monthly_premium_eur": 15.83, "annual_premium_eur": 190.0,
        "deductible_eur": 0.0, "coverage_limit_eur": 5_000_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Travel medical", "Trip cancellation", "Travel luggage", "Liability coverage",
        ],
        "additional_features": ["Worldwide cover", "24/7 helpline"],
        "exclusions": ["High-risk sports", "Pre-existing conditions"],
        "description": "Worldwide travel insurance with no deductible.",
    },
    {
        "provider": "Generali Austria",
        "name": "Reise Komfort",
        "product_line": ProductLine.TRAVEL,
        "monthly_premium_eur": 18.33, "annual_premium_eur": 220.0,
        "deductible_eur": 50.0, "coverage_limit_eur": 7_500_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Travel medical", "Trip cancellation", "Travel luggage",
            "Liability coverage", "Rental car protection",
        ],
        "additional_features": ["Family cover up to 4", "Adventure sports option"],
        "exclusions": ["Racing events"],
        "description": "Family-friendly travel package.",
    },
    {
        "provider": "Donau Versicherung",
        "name": "Reise Basic",
        "product_line": ProductLine.TRAVEL,
        "monthly_premium_eur": 12.5, "annual_premium_eur": 150.0,
        "deductible_eur": 100.0, "coverage_limit_eur": 2_000_000.0,
        "risk_level": RiskLevel.MEDIUM,
        "coverage_items": ["Travel medical", "Travel luggage"],
        "additional_features": [],
        "exclusions": ["Trip cancellation", "High-risk sports"],
        "description": "Entry-level travel cover for short EU trips.",
    },

    # ---- Legal ----
    {
        "provider": "Generali Austria",
        "name": "Privat Schutz",
        "product_line": ProductLine.LEGAL,
        "monthly_premium_eur": 23.33, "annual_premium_eur": 280.0,
        "deductible_eur": 0.0, "coverage_limit_eur": 100_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Legal protection", "Contract disputes", "Tenancy disputes", "Employment disputes",
        ],
        "additional_features": ["Legal helpline", "Mediation support"],
        "exclusions": ["Criminal defence for intentional acts"],
        "description": "Personal legal expenses cover for everyday disputes.",
    },
    {
        "provider": "UNIQA",
        "name": "Recht & Klar",
        "product_line": ProductLine.LEGAL,
        "monthly_premium_eur": 25.0, "annual_premium_eur": 300.0,
        "deductible_eur": 0.0, "coverage_limit_eur": 150_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Legal protection", "Contract disputes", "Traffic legal protection",
            "Tax legal advice",
        ],
        "additional_features": ["Online lawyer chat"],
        "exclusions": ["Disputes with the same insurer"],
        "description": "Legal expenses cover with traffic and tax modules.",
    },
    {
        "provider": "Allianz Austria",
        "name": "Rechtsschutz Family",
        "product_line": ProductLine.LEGAL,
        "monthly_premium_eur": 28.33, "annual_premium_eur": 340.0,
        "deductible_eur": 100.0, "coverage_limit_eur": 200_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": [
            "Legal protection", "Contract disputes", "Tenancy disputes",
            "Employment disputes", "Family law",
        ],
        "additional_features": ["Worldwide coverage"],
        "exclusions": ["Pre-existing disputes"],
        "description": "Family-wide legal protection including family-law cases.",
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed() -> None:
    setup_logging()
    async with AsyncSessionLocal() as db:
        # ---- Providers ----
        existing = (await db.execute(select(Provider))).scalars().all()
        by_name = {p.name: p for p in existing}

        # Migrate any provider still seeded under a legacy short name (from
        # the original 6-provider demo catalogue) onto its real legal name
        # in-place, instead of inserting a duplicate row. Also backfill
        # logo_url/rating_score from the canonical PROVIDERS entry, since the
        # legacy rows predate the logo research.
        canonical_by_name = {p["name"]: p for p in PROVIDERS}
        for legacy_name, legal_name in _LEGACY_PROVIDER_ALIAS.items():
            row = by_name.pop(legacy_name, None)
            if row is None or legal_name in by_name:
                continue
            row.name = legal_name
            canonical = canonical_by_name[legal_name]
            row.logo_url = canonical["logo_url"]
            row.rating_score = canonical["rating_score"]
            by_name[legal_name] = row

        existing_names = set(by_name)
        for entry in PROVIDERS:
            if entry["name"] in existing_names:
                continue
            db.add(Provider(**entry))
        await db.flush()

        provider_lookup = {
            p.name: p for p in (await db.execute(select(Provider))).scalars().all()
        }

        # ---- Policies ----
        existing_policies = {p.name for p in (await db.execute(select(Policy))).scalars().all()}
        for entry in POLICIES:
            if entry["name"] in existing_policies:
                continue
            data = dict(entry)
            provider_name = data.pop("provider")
            provider_name = _LEGACY_PROVIDER_ALIAS.get(provider_name, provider_name)
            provider = provider_lookup[provider_name]
            db.add(Policy(provider_id=provider.id, **data))
        await db.flush()

        # ---- Demo accounts ----
        for email, pw, role in (
            (settings.SEED_DEMO_USER_EMAIL, settings.SEED_DEMO_USER_PASSWORD, UserRole.USER),
            (settings.SEED_DEMO_ADMIN_EMAIL, settings.SEED_DEMO_ADMIN_PASSWORD, UserRole.ADMIN),
        ):
            stmt = select(User).where(User.email == email.lower())
            existing_user = (await db.execute(stmt)).scalar_one_or_none()
            if existing_user:
                continue
            user = User(
                email=email.lower(),
                full_name="Test User" if role is UserRole.USER else "Admin User",
                password_hash=hash_password(pw),
                role=role,
                is_active=True,
            )
            db.add(user)
            await db.flush()

            if role is UserRole.USER:
                db.add(
                    RiskProfile(
                        user_id=user.id,
                        insurance_type=ProductLine.CAR,
                        monthly_budget_eur=100.0,
                        risk_tolerance=RiskTolerance.MEDIUM,
                        coverage_level=CoverageLevel.STANDARD,
                        deductible_preference=DeductiblePreference.MEDIUM,
                        household_size=1,
                        property_value_eur=None,
                        required_coverages=[],
                        weights={},
                    )
                )

        await db.commit()
        logger.info("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())

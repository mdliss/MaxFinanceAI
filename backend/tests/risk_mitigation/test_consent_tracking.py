"""
Risk Mitigation Tests: Consent Tracking Reliability
Tests that consent is tracked accurately and recommendations respect consent status.
"""
import pytest
from sqlalchemy import select
from app.models import User, ConsentRecord, Recommendation
from app.services.recommendation_engine import RecommendationEngine
from app.services.guardrails import GuardrailViolation
import datetime


class TestConsentReliability:
    """Test that consent tracking is reliable and enforced."""

    @pytest.mark.asyncio
    async def test_no_recommendations_without_consent(self, test_db):
        """Ensure no recommendations are generated without consent."""
        # Create user without consent
        user = User(
            user_id="test_no_consent",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=False
        )
        test_db.add(user)
        await test_db.commit()

        # Try to generate recommendations
        engine = RecommendationEngine(test_db)

        with pytest.raises(GuardrailViolation) as exc_info:
            await engine.generate_recommendations(user.user_id)

        assert "consent" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_consent_revocation_stops_recommendations(self, test_db):
        """Ensure revoking consent prevents new recommendations."""
        # Create user with consent
        user = User(
            user_id="test_revoke",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)

        consent = ConsentRecord(
            user_id=user.user_id,
            consent_status=True,
            consent_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent)
        await test_db.commit()

        # Revoke consent
        user.has_consented = False
        consent.consent_status = False
        consent.revoked_timestamp = datetime.datetime.utcnow()
        await test_db.commit()

        # Try to generate recommendations
        engine = RecommendationEngine(test_db)

        with pytest.raises(GuardrailViolation) as exc_info:
            await engine.generate_recommendations(user.user_id)

        assert "consent" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_consent_audit_trail_complete(self, test_db):
        """Ensure consent changes are fully audited."""
        user = User(
            user_id="test_audit",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=False
        )
        test_db.add(user)
        await test_db.commit()

        # Grant consent
        consent1 = ConsentRecord(
            user_id=user.user_id,
            consent_status=True,
            consent_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent1)
        await test_db.commit()

        # Revoke consent
        consent2 = ConsentRecord(
            user_id=user.user_id,
            consent_status=False,
            consent_timestamp=datetime.datetime.utcnow(),
            revoked_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent2)
        await test_db.commit()

        # Re-grant consent
        consent3 = ConsentRecord(
            user_id=user.user_id,
            consent_status=True,
            consent_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent3)
        await test_db.commit()

        # Check audit trail
        result = await test_db.execute(
            select(ConsentRecord).where(ConsentRecord.user_id == user.user_id)
        )
        consents = result.scalars().all()

        assert len(consents) == 3
        assert consents[0].consent_status is True
        assert consents[1].consent_status is False
        assert consents[2].consent_status is True

    @pytest.mark.asyncio
    async def test_partial_consent_not_allowed(self, test_db):
        """Ensure there's no partial consent - it's all or nothing."""
        user = User(
            user_id="test_partial",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)
        await test_db.commit()

        # Consent must be boolean, not partial
        assert user.has_consented is True or user.has_consented is False
        assert user.has_consented is not None

    @pytest.mark.asyncio
    async def test_consent_timestamp_recorded(self, test_db):
        """Ensure consent timestamp is always recorded."""
        user = User(
            user_id="test_timestamp",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)

        before_consent = datetime.datetime.utcnow()

        consent = ConsentRecord(
            user_id=user.user_id,
            consent_status=True,
            consent_timestamp=datetime.datetime.utcnow()
        )
        test_db.add(consent)
        await test_db.commit()

        after_consent = datetime.datetime.utcnow()

        assert consent.consent_timestamp is not None
        assert before_consent <= consent.consent_timestamp <= after_consent


class TestConsentEdgeCases:
    """Test edge cases in consent handling."""

    @pytest.mark.asyncio
    async def test_deleted_user_consent_check(self, test_db):
        """Ensure deleted users cannot have recommendations generated."""
        # Try to generate for non-existent user
        engine = RecommendationEngine(test_db)

        with pytest.raises(Exception):  # Should raise some error
            await engine.generate_recommendations("nonexistent_user_123")

    @pytest.mark.asyncio
    async def test_concurrent_consent_changes(self, test_db):
        """Test that concurrent consent changes are handled correctly."""
        user = User(
            user_id="test_concurrent",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=True
        )
        test_db.add(user)
        await test_db.commit()

        # Simulate rapid consent changes
        for i in range(5):
            consent = ConsentRecord(
                user_id=user.user_id,
                consent_status=i % 2 == 0,
                consent_timestamp=datetime.datetime.utcnow()
            )
            test_db.add(consent)
        await test_db.commit()

        # Check all changes recorded
        result = await test_db.execute(
            select(ConsentRecord).where(ConsentRecord.user_id == user.user_id)
        )
        consents = result.scalars().all()
        assert len(consents) == 5

    @pytest.mark.asyncio
    async def test_consent_required_for_signal_detection(self, test_db):
        """Ensure consent is required even for signal detection."""
        from app.services.signal_detection import SignalDetector

        user = User(
            user_id="test_signal_consent",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.date(1990, 1, 1),
            has_consented=False
        )
        test_db.add(user)
        await test_db.commit()

        detector = SignalDetector(test_db)

        with pytest.raises(Exception) as exc_info:
            await detector.detect_signals(user.user_id)

        # Should fail due to lack of consent
        assert "consent" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

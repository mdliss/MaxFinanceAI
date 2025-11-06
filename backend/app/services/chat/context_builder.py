from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import User, Transaction, Signal, Recommendation, Persona, Account
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import tiktoken


class ContextBuilder:
    """Builds rich financial context from user data for LLM prompts."""

    def __init__(self, db: AsyncSession):
        """Initialize context builder.

        Args:
            db: Database session
        """
        self.db = db
        # Use tiktoken for accurate token counting (similar to Claude/GPT)
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            # Fallback if tiktoken not available
            self.encoder = None

    async def build_context(self, user_id: str, max_tokens: int = 6000) -> str:
        """Build comprehensive financial context for a user.

        Gathers profile, transactions, signals, recommendations, and formats
        them into a concise text summary for LLM consumption.

        Args:
            user_id: User ID
            max_tokens: Maximum tokens to use (will truncate if exceeded)

        Returns:
            Formatted context string
        """
        # Fetch all data in parallel for performance
        profile = await self._get_profile(user_id)
        accounts = await self._get_accounts(user_id)
        transactions = await self._get_recent_transactions(user_id, limit=20)
        signals = await self._get_signals(user_id)
        recommendations = await self._get_recommendations(user_id)
        personas = await self._get_personas(user_id)
        spending_summary = await self._get_spending_summary(user_id)

        # Build context sections
        context_parts = [
            self._format_profile(profile, accounts),
            self._format_spending_summary(spending_summary),
            self._format_signals(signals),
            self._format_recommendations(recommendations),
            self._format_recent_transactions(transactions),
            self._format_personas(personas)
        ]

        # Join sections
        context = "\n\n".join([part for part in context_parts if part])

        # Check token count and truncate if needed
        if self.encoder:
            tokens = len(self.encoder.encode(context))
            while tokens > max_tokens and len(transactions) > 5:
                # Remove oldest transactions to reduce tokens
                transactions = transactions[:-5]
                context_parts[4] = self._format_recent_transactions(transactions)
                context = "\n\n".join([part for part in context_parts if part])
                tokens = len(self.encoder.encode(context))

        return context

    async def _get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data."""
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        return {
            "name": user.name,
            "age": user.age,
            "income_level": user.income_level,
            "consent_status": user.consent_status
        }

    async def _get_accounts(self, user_id: str) -> List[Dict]:
        """Get user's account information."""
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        accounts = result.scalars().all()

        return [
            {
                "account_type": acc.type,
                "balance": float(acc.current_balance) if acc.current_balance else 0,
                "credit_limit": float(acc.credit_limit) if acc.credit_limit else None
            }
            for acc in accounts
        ]

    async def _get_recent_transactions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent transactions (last 30 days)."""
        cutoff = datetime.now() - timedelta(days=30)
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .where(Transaction.date >= cutoff)
            .order_by(Transaction.date.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()

        return [
            {
                "date": txn.date.strftime("%Y-%m-%d"),
                "merchant": txn.merchant_name,
                "category": txn.category_primary or "Other",
                "amount": float(txn.amount)
            }
            for txn in transactions
        ]

    async def _get_signals(self, user_id: str) -> List[Dict]:
        """Get behavioral signals."""
        result = await self.db.execute(
            select(Signal)
            .where(Signal.user_id == user_id)
            .order_by(Signal.computed_at.desc())
        )
        signals = result.scalars().all()

        return [
            {
                "type": sig.signal_type,
                "value": float(sig.value),
                "details": sig.details
            }
            for sig in signals
        ]

    async def _get_recommendations(self, user_id: str) -> List[Dict]:
        """Get approved recommendations."""
        result = await self.db.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .where(Recommendation.approval_status == "approved")
            .order_by(Recommendation.created_at.desc())
            .limit(5)
        )
        recs = result.scalars().all()

        return [
            {
                "title": rec.title,
                "description": rec.description,
                "rationale": rec.rationale,
                "persona_type": rec.persona_type
            }
            for rec in recs
        ]

    async def _get_personas(self, user_id: str) -> List[Dict]:
        """Get user's personas."""
        result = await self.db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.priority_rank)
        )
        personas = result.scalars().all()

        return [
            {
                "type": p.persona_type,
                "priority": p.priority_rank,
                "criteria_met": p.criteria_met
            }
            for p in personas
        ]

    async def _get_spending_summary(self, user_id: str) -> Dict[str, float]:
        """Calculate spending by category (last 30 days)."""
        cutoff = datetime.now() - timedelta(days=30)
        result = await self.db.execute(
            select(
                Transaction.category_primary,
                func.sum(Transaction.amount).label("total")
            )
            .where(Transaction.user_id == user_id)
            .where(Transaction.date >= cutoff)
            .group_by(Transaction.category_primary)
            .order_by(func.sum(Transaction.amount).desc())
        )

        return {row[0]: float(row[1]) for row in result.all()}

    def _format_profile(self, profile: Optional[Dict], accounts: List[Dict]) -> str:
        """Format user profile for LLM."""
        if not profile:
            return "USER PROFILE: Not available"

        # Calculate total balances
        checking_balance = sum(a["balance"] for a in accounts if a["account_type"] == "checking")
        savings_balance = sum(a["balance"] for a in accounts if a["account_type"] == "savings")
        credit_cards = [a for a in accounts if a["account_type"] == "credit"]

        profile_text = f"""USER PROFILE:
- Name: {profile['name']}
- Age: {profile.get('age', 'N/A')}
- Income Level: {profile.get('income_level', 'N/A')}

ACCOUNTS:
- Checking Balance: ${checking_balance:,.2f}
- Savings Balance: ${savings_balance:,.2f}"""

        if credit_cards:
            for i, cc in enumerate(credit_cards, 1):
                util = (cc["balance"] / cc["credit_limit"] * 100) if cc["credit_limit"] else 0
                profile_text += f"\n- Credit Card {i}: ${cc['balance']:,.2f} / ${cc['credit_limit']:,.2f} ({util:.1f}% utilization)"

        return profile_text

    def _format_spending_summary(self, spending: Dict[str, float]) -> str:
        """Format spending summary for LLM."""
        if not spending:
            return ""

        summary = "SPENDING LAST 30 DAYS:"
        total = sum(spending.values())
        summary += f"\n- Total: ${total:,.2f}"

        for category, amount in list(spending.items())[:5]:  # Top 5 categories
            pct = (amount / total * 100) if total > 0 else 0
            summary += f"\n- {category.title()}: ${amount:,.2f} ({pct:.1f}%)"

        return summary

    def _format_signals(self, signals: List[Dict]) -> str:
        """Format behavioral signals for LLM."""
        if not signals:
            return ""

        signals_text = "BEHAVIORAL SIGNALS:"

        for sig in signals:
            sig_type = sig["type"]
            details = sig["details"] or {}

            if sig_type == "credit_utilization":
                util = details.get("utilization_percent", sig["value"])
                signals_text += f"\n- Credit Utilization: {util:.1f}% "
                if util > 30:
                    signals_text += "(⚠️ Above recommended 30%)"
                else:
                    signals_text += "(✓ Healthy)"

            elif sig_type == "income_stability":
                status = details.get("status", "unknown")
                avg = details.get("average_income", 0)
                signals_text += f"\n- Income: ${avg:,.2f}/month ({status})"

            elif sig_type == "spending_surge":
                category = details.get("category", "unknown")
                amount = details.get("total_spent", 0)
                avg = details.get("average_spending", 0)
                pct = ((amount - avg) / avg * 100) if avg > 0 else 0
                signals_text += f"\n- Spending Surge in {category}: ${amount:,.2f} (+{pct:.0f}% vs average)"

            elif sig_type == "subscription_detected":
                merchant = details.get("merchant_name", "unknown")
                monthly = details.get("monthly_amount", 0)
                signals_text += f"\n- Subscription: {merchant} (${monthly:.2f}/month)"

            elif sig_type == "savings_growth":
                rate = details.get("growth_rate", sig["value"])
                signals_text += f"\n- Savings Growth: {rate:.1f}% per month"

        return signals_text

    def _format_recommendations(self, recs: List[Dict]) -> str:
        """Format recommendations for LLM."""
        if not recs:
            return ""

        rec_text = f"PERSONALIZED RECOMMENDATIONS ({len(recs)} active):"

        for i, rec in enumerate(recs, 1):
            rec_text += f"\n{i}. {rec['title']} ({rec['persona_type']})"
            rec_text += f"\n   {rec['description']}"
            if rec['rationale']:
                rec_text += f"\n   Why: {rec['rationale']}"

        return rec_text

    def _format_recent_transactions(self, transactions: List[Dict]) -> str:
        """Format recent transactions for LLM."""
        if not transactions:
            return ""

        txn_text = f"RECENT TRANSACTIONS (Last 30 days, showing {len(transactions)}):"

        # Group by category for summary
        by_category = {}
        for txn in transactions:
            cat = txn["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(txn)

        # Show summary by category
        for category, txns in by_category.items():
            total = sum(t["amount"] for t in txns)
            count = len(txns)
            txn_text += f"\n- {category.title()}: {count} transactions, ${total:,.2f} total"

        # Show individual recent transactions
        txn_text += "\n\nMost Recent:"
        for txn in transactions[:10]:  # Show last 10
            txn_text += f"\n  {txn['date']}: {txn['merchant']} - ${txn['amount']:.2f} ({txn['category']})"

        return txn_text

    def _format_personas(self, personas: List[Dict]) -> str:
        """Format personas for LLM."""
        if not personas:
            return ""

        persona_text = "USER PERSONAS:"
        for p in personas:
            persona_text += f"\n- {p['type'].replace('_', ' ').title()} (Priority: {p['priority']})"

        return persona_text

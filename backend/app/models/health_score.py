from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class HealthScore(Base):
    """Model for user financial health scores"""
    __tablename__ = "health_scores"

    score_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    overall_score = Column(Integer, nullable=False, index=True)  # 0-100
    savings_score = Column(Integer)  # 0-100
    spending_score = Column(Integer)  # 0-100
    debt_score = Column(Integer)  # 0-100
    emergency_fund_score = Column(Integer)  # 0-100
    budget_adherence_score = Column(Integer)  # 0-100
    score_trend = Column(String)  # improving, declining, stable
    recommendations_applied_count = Column(Integer, default=0)
    days_since_last_calculation = Column(Integer, default=0)
    meta_data = Column(Text)  # JSON string with detailed breakdown
    computed_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="health_scores")

    def __repr__(self):
        return f"<HealthScore {self.score_id}: User {self.user_id} - {self.overall_score}/100>"

    def to_dict(self):
        """Convert health score to dictionary for API responses"""
        return {
            "score_id": self.score_id,
            "user_id": self.user_id,
            "overall_score": self.overall_score,
            "savings_score": self.savings_score,
            "spending_score": self.spending_score,
            "debt_score": self.debt_score,
            "emergency_fund_score": self.emergency_fund_score,
            "budget_adherence_score": self.budget_adherence_score,
            "score_trend": self.score_trend,
            "recommendations_applied_count": self.recommendations_applied_count,
            "days_since_last_calculation": self.days_since_last_calculation,
            "metadata": self.meta_data,  # Expose as 'metadata' in API
            "computed_at": self.computed_at.isoformat() if self.computed_at else None
        }

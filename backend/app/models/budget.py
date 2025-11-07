from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Budget(Base):
    """Model for user budgets"""
    __tablename__ = "budgets"

    budget_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    category = Column(String, nullable=False, index=True)  # dining, transportation, shopping, entertainment, etc.
    amount = Column(Float, nullable=False)
    period = Column(String, default="monthly")  # weekly, monthly, yearly
    spent_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    status = Column(String, default="active", index=True)  # active, exceeded, warning, inactive
    is_auto_generated = Column(Boolean, default=False)
    rollover_enabled = Column(Boolean, default=False)
    alert_threshold = Column(Float, default=80.0)  # Alert when spent reaches this % of budget
    period_start_date = Column(String, index=True)  # ISO 8601 date
    period_end_date = Column(String, index=True)  # ISO 8601 date
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="budgets")

    def __repr__(self):
        return f"<Budget {self.budget_id}: {self.category} ${self.amount}/{self.period}>"

    def to_dict(self):
        """Convert budget to dictionary for API responses"""
        return {
            "budget_id": self.budget_id,
            "user_id": self.user_id,
            "category": self.category,
            "amount": self.amount,
            "period": self.period,
            "spent_amount": self.spent_amount,
            "remaining_amount": self.remaining_amount,
            "status": self.status,
            "is_auto_generated": self.is_auto_generated,
            "rollover_enabled": self.rollover_enabled,
            "alert_threshold": self.alert_threshold,
            "period_start_date": self.period_start_date,
            "period_end_date": self.period_end_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

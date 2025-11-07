from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Subscription(Base):
    """Model for tracked subscriptions"""
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    merchant_name = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    frequency = Column(String, default="monthly")  # weekly, monthly, quarterly, yearly
    category = Column(String)
    next_billing_date = Column(String, index=True)  # ISO 8601 date
    status = Column(String, default="active", index=True)  # active, cancelled, paused
    auto_detected = Column(Boolean, default=True)  # True = auto-detected, False = manually added
    first_detected_date = Column(String)
    last_transaction_date = Column(String)
    transaction_count = Column(Integer, default=0)
    annual_cost = Column(Float)  # Calculated annual cost
    cancellation_difficulty = Column(String)  # easy, medium, hard
    cancellation_url = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription {self.subscription_id}: {self.merchant_name} ${self.amount}/{self.frequency}>"

    def to_dict(self):
        """Convert subscription to dictionary for API responses"""
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "merchant_name": self.merchant_name,
            "amount": self.amount,
            "frequency": self.frequency,
            "category": self.category,
            "next_billing_date": self.next_billing_date,
            "status": self.status,
            "auto_detected": self.auto_detected,
            "first_detected_date": self.first_detected_date,
            "last_transaction_date": self.last_transaction_date,
            "transaction_count": self.transaction_count,
            "annual_cost": self.annual_cost,
            "cancellation_difficulty": self.cancellation_difficulty,
            "cancellation_url": self.cancellation_url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

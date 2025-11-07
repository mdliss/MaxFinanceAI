from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class FinancialGoal(Base):
    """Model for user financial goals"""
    __tablename__ = "financial_goals"

    goal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    goal_type = Column(String, nullable=False)  # emergency_fund, vacation, debt_payoff, major_purchase, retirement, custom
    title = Column(String, nullable=False)
    description = Column(String)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(String)  # ISO 8601 date
    status = Column(String, default="active")  # active, completed, paused, cancelled
    progress_percent = Column(Float, default=0.0)
    projected_completion_date = Column(String)  # ISO 8601 date, calculated
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<FinancialGoal {self.goal_id}: {self.title} ({self.progress_percent}% complete)>"

    def to_dict(self):
        """Convert goal to dictionary for API responses"""
        return {
            "goal_id": self.goal_id,
            "user_id": self.user_id,
            "goal_type": self.goal_type,
            "title": self.title,
            "description": self.description,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "target_date": self.target_date,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "projected_completion_date": self.projected_completion_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

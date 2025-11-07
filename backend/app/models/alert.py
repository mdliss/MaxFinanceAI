from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Alert(Base):
    """Model for user alerts and notifications"""
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False, index=True)  # budget_exceeded, unusual_spending, goal_milestone, subscription_renewal, low_balance
    severity = Column(String, default="info", index=True)  # info, warning, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    related_entity_type = Column(String)  # budget, goal, transaction, subscription, account
    related_entity_id = Column(String)
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False)
    action_url = Column(String)  # Optional link to related entity
    meta_data = Column(Text)  # JSON string for additional data
    created_at = Column(DateTime, server_default=func.now(), index=True)
    read_at = Column(DateTime)
    dismissed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="alerts")

    def __repr__(self):
        return f"<Alert {self.alert_id}: {self.alert_type} ({self.severity})>"

    def to_dict(self):
        """Convert alert to dictionary for API responses"""
        return {
            "alert_id": self.alert_id,
            "user_id": self.user_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "action_url": self.action_url,
            "metadata": self.meta_data,  # Expose as 'metadata' in API
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None
        }

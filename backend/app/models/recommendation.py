from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    persona_type = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    rationale = Column(Text, nullable=False)
    disclaimer = Column(Text)
    eligibility_met = Column(Boolean, default=True)
    approval_status = Column(String, default="pending")
    operator_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation {self.recommendation_id}: {self.title}>"

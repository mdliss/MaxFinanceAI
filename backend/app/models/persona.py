from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Persona(Base):
    __tablename__ = "personas"

    persona_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    window_days = Column(Integer, nullable=False)
    persona_type = Column(String, nullable=False, index=True)
    priority_rank = Column(Integer)
    criteria_met = Column(String)
    assigned_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="personas")

    def __repr__(self):
        return f"<Persona {self.persona_type} for user {self.user_id}>"

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog {self.log_id}: {self.action} by {self.actor}>"

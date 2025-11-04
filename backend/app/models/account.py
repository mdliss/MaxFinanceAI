from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    subtype = Column(String)
    available_balance = Column(Float)
    current_balance = Column(Float)
    credit_limit = Column(Float)
    iso_currency_code = Column(String, default="USD")
    holder_category = Column(String)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account {self.account_id}: {self.type}>"

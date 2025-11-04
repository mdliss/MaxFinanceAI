from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's full name")
    age: Optional[int] = Field(None, description="User's age")
    income_level: Optional[str] = Field(None, description="User's income level")

class UserCreate(UserBase):
    pass

class ConsentRequest(BaseModel):
    user_id: str = Field(..., description="User ID granting consent")
    consent_status: bool = Field(..., description="Consent status")

class ConsentResponse(BaseModel):
    user_id: str
    consent_status: bool
    consent_timestamp: Optional[datetime]
    message: str

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    consent_status: bool
    consent_timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

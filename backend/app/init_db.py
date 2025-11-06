import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app.config import settings

# Import all models to ensure they are registered with Base
from app.models import (
    User,
    Account,
    Transaction,
    Liability,
    Signal,
    Persona,
    Recommendation,
    AuditLog,
    Feedback,
    ChatMessage,
    ChatFeedback,
)

async def init_database():
    """Initialize the database and create all tables."""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # Drop all tables (for development)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Database initialized successfully!")
    print(f"Created tables: {', '.join(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    asyncio.run(init_database())

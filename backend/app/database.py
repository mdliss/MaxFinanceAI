from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
import os
from pathlib import Path

# Extract database directory from URL and ensure it exists
# Database URL format: sqlite+aiosqlite:////app/data/spendsense.db
db_url = settings.database_url
if "sqlite" in db_url:
    # Extract path from sqlite URL (remove sqlite+aiosqlite:/// prefix)
    db_path = db_url.split("sqlite+aiosqlite:///")[-1]
    db_dir = str(Path(db_path).parent)

    # Handle Railway volume mount (where /app/data might exist as a file)
    if os.path.exists(db_dir) and os.path.isfile(db_dir):
        print(f"⚠️  {db_dir} exists as a file, removing it to create directory")
        os.remove(db_dir)

    os.makedirs(db_dir, exist_ok=True)
    print(f"📁 Database directory: {db_dir}")
    print(f"📊 Database file: {db_path}")

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False}
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency for getting database session
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

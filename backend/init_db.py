#!/usr/bin/env python3
"""Initialize database with tables and demo data"""
import asyncio
from app.database import engine, Base

async def init_database():
    """Create all tables if they don't exist"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Dispose engine to ensure all writes are flushed
    await engine.dispose()

    print("✅ Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_database())

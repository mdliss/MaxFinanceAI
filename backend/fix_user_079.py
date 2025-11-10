#!/usr/bin/env python3
import asyncio
from sqlalchemy import select, delete
from app.database import async_session_maker
from app.models import User, Signal
from app.services.signal_detector import SignalDetector

async def main():
    async with async_session_maker() as db:
        # Delete user_079's signals
        await db.execute(delete(Signal).where(Signal.user_id == 'user_079'))
        await db.commit()
        
        # Re-detect
        detector = SignalDetector(db)
        signals = await detector.detect_all_signals('user_079', window_days=180)
        
        for signal in signals:
            db.add(signal)
        
        await db.commit()
        
        print(f"✅ Added {len(signals)} signals for user_079:")
        for s in signals:
            print(f"  - {s.signal_type}: {s.value}")

if __name__ == "__main__":
    asyncio.run(main())

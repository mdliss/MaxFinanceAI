#!/usr/bin/env python3
"""Re-run signal detection for all users to fix coverage."""
import asyncio
from sqlalchemy import select, delete
from app.database import async_session_maker, engine, Base
from app.models import User, Signal
from app.services.signal_detector import SignalDetector

async def main():
    print("Re-detecting signals for all users...")
   
    async with async_session_maker() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users")
        
        # Delete existing signals
        await db.execute(delete(Signal))
        await db.commit()
        print("Deleted old signals")
        
        # Re-detect for each user
        detector = SignalDetector(db)
        
        for idx, user in enumerate(users, 1):
            signals = await detector.detect_all_signals(user.user_id, window_days=180)
            
            for signal in signals:
                db.add(signal)
            
            if idx % 10 == 0:
                print(f"Processed {idx}/{len(users)} users...")
        
        await db.commit()
        
        # Count new signals
        result = await db.execute(select(Signal))
        new_signals = result.scalars().all()
        
        print(f"\n✅ Re-detection complete!")
        print(f"Total signals created: {len(new_signals)}")
        
        # Count by type
        from collections import Counter
        signal_types = Counter(s.signal_type for s in new_signals)
        print("\nSignals by type:")
        for signal_type, count in signal_types.items():
            print(f"  {signal_type}: {count}")

if __name__ == "__main__":
    asyncio.run(main())

"""
Script to add sentiment_score column to reviews table.
Run this once to migrate the existing database.
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.core.logging import get_logger

logger = get_logger(__name__)


async def add_sentiment_column():
    """Add sentiment_score column to reviews table if it doesn't exist."""
    async with engine.begin() as conn:
        # Check if column exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='reviews' AND column_name='sentiment_score';
        """)

        result = await conn.execute(check_query)
        column_exists = result.fetchone() is not None

        if not column_exists:
            logger.info("Adding sentiment_score column to reviews table...")
            alter_query = text("""
                ALTER TABLE reviews
                ADD COLUMN sentiment_score FLOAT;
            """)
            await conn.execute(alter_query)
            logger.info("✅ sentiment_score column added successfully!")
        else:
            logger.info("sentiment_score column already exists, skipping...")


async def main():
    """Main function."""
    try:
        await add_sentiment_column()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

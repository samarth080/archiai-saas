import argparse
import asyncio

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.user import User
from app.services.layout_pattern_seed_service import (
    SEED_SOURCE_URL,
    seed_mvp_layout_patterns,
)


async def seed_layout_patterns(user_email: str) -> None:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == user_email))
        if user is None:
            raise SystemExit(
                f"User '{user_email}' was not found. Register locally before seeding."
            )

        result = await seed_mvp_layout_patterns(db, created_by=user.id)
        print(
            f"Seed source: {SEED_SOURCE_URL}\n"
            f"Created: {result.created}\n"
            f"Already present: {result.existing}\n"
            f"Expected total: {result.total}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed clearly labeled MVP layout patterns for local development."
    )
    parser.add_argument(
        "--user-email",
        required=True,
        help="Email of an existing local ArchiAI user recorded as the seed source creator.",
    )
    args = parser.parse_args()
    asyncio.run(seed_layout_patterns(args.user_email))


if __name__ == "__main__":
    main()

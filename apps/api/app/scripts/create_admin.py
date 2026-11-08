import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import StudentProfile, User, UserRole


async def create_or_promote_admin(email: str, password: str, full_name: str = "System Admin") -> None:
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email.lower())
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f"User {email} already exists. Promoting to admin...")
            user.role = UserRole.ADMIN
            user.is_verified = True
            if password:
                user.password_hash = hash_password(password)
            await session.commit()
            print(f"User {email} successfully updated to role 'admin'.")
            return

        print(f"Creating new admin user: {email}...")
        new_admin = User(
            email=email.lower(),
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_verified=True,
        )
        session.add(new_admin)
        await session.flush()

        profile = StudentProfile(
            user_id=new_admin.id,
            full_name=full_name,
            timezone="UTC",
            target_countries=[],
            fields_of_interest=[],
        )
        session.add(profile)
        await session.commit()
        print(f"Admin account successfully created for {email} (ID: {new_admin.id}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote an OpportunityAbroad admin user.")
    parser.add_argument("--email", required=True, help="Admin user email address")
    parser.add_argument("--password", required=True, help="Admin user password (min 8 chars)")
    parser.add_argument("--name", default="System Administrator", help="Admin display name")

    args = parser.parse_args()

    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(create_or_promote_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()

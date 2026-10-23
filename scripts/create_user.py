import argparse, getpass
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from argon2 import PasswordHasher
from app.database import DB, User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument(
        "--role", choices=["admin", "investigator"], default="investigator"
    )
    args = parser.parse_args()
    command.upgrade(Config("alembic.ini"), "head")
    password = getpass.getpass("Password (at least 12 characters): ")
    if len(password) < 12 or password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords must match and contain at least 12 characters")
    with DB() as db:
        if db.scalar(select(User).where(User.username == args.username)):
            raise SystemExit("User already exists")
        db.add(
            User(
                username=args.username,
                password=PasswordHasher().hash(password),
                role=args.role,
            )
        )
        db.commit()
    print("User created")


if __name__ == "__main__":
    main()

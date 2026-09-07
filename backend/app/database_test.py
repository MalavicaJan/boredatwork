from sqlalchemy import text

from app.database import engine


with engine.connect() as connection:
    result = connection.execute(
        text("SELECT current_user, current_database(), version()")
    )
    row = result.fetchone()

    print("Database connection successful!")
    print(f"User: {row[0]}")
    print(f"Database: {row[1]}")
    print(f"PostgreSQL: {row[2]}")

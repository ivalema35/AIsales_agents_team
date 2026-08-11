from database.db_config import engine


def run():
    with engine.begin() as conn:
        with open("database/schema.sql", "r", encoding="utf-8") as f:
            conn.connection.executescript(f.read())
    print("Schema applied.")


if __name__ == "__main__":
    run()

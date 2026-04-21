import argparse

from storage import SQLiteStorage


def main():
    parser = argparse.ArgumentParser(description="Initialize the chess database schema")
    parser.add_argument("--db-path", default="data/chess.db", help="Path to SQLite database file")
    args = parser.parse_args()

    storage = SQLiteStorage(db_path=args.db_path)
    storage.close()
    print(f"Database initialized at {args.db_path}")


if __name__ == "__main__":
    main()

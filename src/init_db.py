import argparse

from storage import SQLiteStorage


def main():
    parser = argparse.ArgumentParser(description="Initialize the chess database schema")
    parser.add_argument(
        "--db-path",
        default=None,
        help=(
            "Path to SQLite database file. "
            "Defaults to CHESS_DB_PATH or the project data/chess.db path."
        ),
    )
    args = parser.parse_args()

    storage = None
    try:
        storage = SQLiteStorage(db_path=args.db_path)
        storage.ensure_schema()
        print(f"Database initialized at {storage.db_path}")
    finally:
        if storage is not None:
            storage.close()


if __name__ == "__main__":
    main()

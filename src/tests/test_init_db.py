import sys
import unittest
from unittest.mock import Mock, patch

import init_db


class TestInitDb(unittest.TestCase):
    def test_main_initializes_schema_and_closes_storage(self):
        storage = Mock()
        storage.db_path = "/tmp/chess.db"

        with patch("init_db.SQLiteStorage", return_value=storage) as storage_class, patch(
            "builtins.print"
        ) as print_mock, patch.object(sys, "argv", ["init_db.py", "--db-path", "/tmp/chess.db"]):
            init_db.main()

        storage_class.assert_called_once_with(db_path="/tmp/chess.db")
        storage.ensure_schema.assert_called_once()
        storage.close.assert_called_once()
        print_mock.assert_called_once_with("Database initialized at /tmp/chess.db")

    def test_main_closes_storage_even_if_schema_initialization_fails(self):
        storage = Mock()
        storage.ensure_schema.side_effect = RuntimeError("boom")

        with patch("init_db.SQLiteStorage", return_value=storage), patch.object(
            sys, "argv", ["init_db.py"]
        ):
            with self.assertRaises(RuntimeError):
                init_db.main()

        storage.close.assert_called_once()

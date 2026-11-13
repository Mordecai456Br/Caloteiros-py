import json
import unittest
from unittest.mock import patch

from app.core.exceptions import DatabaseConnectionError
from app.routers.health import health_check


class HealthCheckTests(unittest.TestCase):
    @patch("app.routers.health.check_database_connection", return_value=True)
    def test_database_connected(self, check_connection):
        self.assertEqual(
            health_check(), {"status": "ok", "database": "connected"}
        )
        check_connection.assert_called_once_with()

    @patch("app.routers.health.check_database_connection")
    def test_database_failure_is_logged_without_exposing_details(self, check_connection):
        check_connection.side_effect = DatabaseConnectionError("internal database details")

        with self.assertLogs("app.routers.health", level="ERROR") as logs:
            response = health_check()

        check_connection.assert_called_once_with()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            json.loads(response.body),
            {
                "status": "error",
                "database": "disconnected",
                "detail": "Erro ao conectar com o banco de dados.",
            },
        )
        self.assertIn("internal database details", "\n".join(logs.output))
        self.assertIsNotNone(logs.records[0].exc_info)

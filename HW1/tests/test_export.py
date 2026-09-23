"""Check the public snapshot contract and last-good-file failure behavior."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import export_weather
from weather import WeatherError, WeatherStore, demo_payload


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / "docs" / "data" / "forecast.json"
        self.db = self.root / "data" / "weather.db"

    def args(self):
        return ["--output", str(self.output), "--db", str(self.db)]

    def write_existing(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_text('{"last": "good"}\n', encoding="utf-8")
        return self.output.read_bytes()

    def test_demo_is_labeled_and_saved_before_export(self):
        with patch.dict("os.environ", {}, clear=True):
            snapshot = export_weather.export_snapshot(output=self.output, db=self.db, demo=True)
        published = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(snapshot, published)
        self.assertEqual(published["dataset"], "F-C0032-001")
        self.assertEqual(published["source"], "demo")
        self.assertEqual(len(published["rows"]), 66)
        self.assertEqual(len({row["city"] for row in published["rows"]}), 22)
        self.assertTrue(published["fetched_at"].endswith("+08:00"))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o644)
        self.assertEqual(WeatherStore(self.db).latest("demo")["rows"], published["rows"])
        self.assertTrue(published["history"])
        required = {"city", "start", "end", "weather", "weather_code", "min_temp",
                    "max_temp", "rain_probability", "comfort"}
        self.assertTrue(all(required <= set(row) for row in published["rows"]))

    def test_missing_key_preserves_snapshot_and_does_not_create_db(self):
        original = self.write_existing()
        with patch.dict("os.environ", {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(export_weather.main(self.args()), 1)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertFalse(self.db.exists())

    def test_live_failure_is_not_replaced_with_demo_and_does_not_leak_key(self):
        original = self.write_existing()
        key = "sensitive-test-key"
        error_output = io.StringIO()
        with patch.dict("os.environ", {"CWA_API_KEY": key}, clear=True), \
                patch("export_weather.fetch_forecast", side_effect=WeatherError(key)), \
                patch("export_weather.demo_payload") as demo, \
                contextlib.redirect_stderr(error_output):
            self.assertEqual(export_weather.main(self.args()), 1)
        self.assertNotIn(key, error_output.getvalue())
        demo.assert_not_called()
        self.assertEqual(self.output.read_bytes(), original)
        self.assertFalse(self.db.exists())

    def test_live_snapshot_uses_cwa_label_without_exporting_credentials(self):
        key = "sensitive-test-key"
        # A mock API fixture exercises the live path without network or real weather.
        fixture = demo_payload()
        fixture["result"]["resource_id"] = "F-C0032-001"
        fixture["records"]["datasetDescription"] = "Mock API fixture"
        with patch.dict("os.environ", {"CWA_API_KEY": key}, clear=True), \
                patch("export_weather.fetch_forecast", return_value=fixture) as fetch:
            snapshot = export_weather.export_snapshot(output=self.output, db=self.db)
        fetch.assert_called_once_with(key)
        self.assertEqual(snapshot["source"], "cwa")
        self.assertNotIn(key, self.output.read_text(encoding="utf-8"))

    def test_malformed_live_response_preserves_snapshot(self):
        original = self.write_existing()
        with patch.dict("os.environ", {"CWA_API_KEY": "test-key"}, clear=True), \
                patch("export_weather.fetch_forecast", return_value={}), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(export_weather.main(self.args()), 1)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertFalse(self.db.exists())

    def test_demo_marker_cannot_be_published_as_live(self):
        original = self.write_existing()
        with patch.dict("os.environ", {"CWA_API_KEY": "test-key"}, clear=True), \
                patch("export_weather.fetch_forecast", return_value=demo_payload()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(export_weather.main(self.args()), 1)
        self.assertEqual(self.output.read_bytes(), original)

    def test_atomic_replace_failure_keeps_prior_file_and_removes_temp(self):
        original = self.write_existing()
        with patch("export_weather.os.replace", side_effect=OSError("write failed")):
            with self.assertRaises(OSError):
                export_weather.atomic_write_json(self.output, {"replacement": True})
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.output.parent.glob(".*.tmp")), [])


if __name__ == "__main__":
    unittest.main()

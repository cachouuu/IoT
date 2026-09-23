"""Offline contract tests; no real API key or network access is required."""

import copy
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import weather


NOW = datetime(2026, 9, 24, 9, 15, tzinfo=weather.TAIPEI)


def fixture():
    payload = weather.demo_payload(NOW)
    payload["result"]["resource_id"] = "F-C0032-001"
    payload["records"]["location"] = payload["records"]["location"][:1]
    return payload


class ForecastTests(unittest.TestCase):
    def test_demo_22_cities_three_deterministic_aware_periods(self):
        payload = weather.demo_payload(NOW)
        self.assertEqual(payload, weather.demo_payload(NOW))
        rows = weather.parse_forecast(payload)
        self.assertEqual(len(rows), 66)
        self.assertEqual({row["city"] for row in rows}, set(weather.CITIES))
        for city in weather.CITIES:
            self.assertEqual(sum(row["city"] == city for row in rows), 3)
        self.assertTrue(all(row["start"].endswith("+08:00") for row in rows))
        self.assertTrue(all(row["end"].endswith("+08:00") for row in rows))
        self.assertIn("非真實", payload["records"]["datasetDescription"])

    def test_join_by_exact_interval_not_array_order(self):
        payload = fixture()
        expected = weather.parse_forecast(payload)
        for element in payload["records"]["location"][0]["weatherElement"]:
            element["time"].reverse()
        payload["records"]["location"][0]["weatherElement"].reverse()
        self.assertEqual(weather.parse_forecast(payload), expected)

    def test_missing_element_and_parameter_are_none(self):
        payload = fixture()
        elements = payload["records"]["location"][0]["weatherElement"]
        elements[:] = [element for element in elements if element["elementName"] != "PoP"]
        next(element for element in elements if element["elementName"] == "MinT")["time"][0].pop("parameter")
        rows = weather.parse_forecast(payload)
        self.assertTrue(all(row["rain_probability"] is None for row in rows))
        self.assertIsNone(rows[0]["min_temp"])
        self.assertIsNotNone(rows[0]["max_temp"])

    def test_different_interval_is_not_combined(self):
        payload = fixture()
        rain = payload["records"]["location"][0]["weatherElement"][1]["time"]
        rain[0]["endTime"] = "2026-09-24 12:00:00"
        rows = weather.parse_forecast(payload)
        self.assertEqual(len(rows), 4)
        short = next(row for row in rows if row["end"] == "2026-09-24T12:00:00+08:00")
        self.assertEqual(short["rain_probability"], 0)
        self.assertIsNone(short["weather"])
        long = next(row for row in rows if row["end"] == "2026-09-24T18:00:00+08:00")
        self.assertIsNone(long["rain_probability"])
        self.assertIsNotNone(long["weather"])

    def test_unknown_element_ignored(self):
        payload = fixture()
        expected = weather.parse_forecast(payload)
        payload["records"]["location"][0]["weatherElement"].append({"elementName": "NewField", "future": "anything"})
        self.assertEqual(weather.parse_forecast(payload), expected)

    def test_malformed_element_name_and_duplicate_city_rejected(self):
        payload = fixture()
        payload["records"]["location"][0]["weatherElement"][0]["elementName"] = []
        with self.assertRaises(weather.WeatherError):
            weather.parse_forecast(payload)
        payload = fixture()
        duplicate = copy.deepcopy(payload["records"]["location"][0])
        duplicate["locationName"] = " " + duplicate["locationName"]
        payload["records"]["location"].append(duplicate)
        with self.assertRaises(weather.WeatherError):
            weather.parse_forecast(payload)

    def test_explicit_offsets_are_normalized(self):
        payload = fixture()
        period = payload["records"]["location"][0]["weatherElement"][0]["time"][0]
        period.update(startTime="2026-09-23T22:00:00Z", endTime="2026-09-24T10:00:00Z")
        self.assertEqual(len(weather.parse_forecast(payload)), 3)

    def test_malformed_and_failure_payloads_rejected(self):
        for payload in (None, [], {}, {"success": "false"}, {"success": "true", "records": {"location": []}}):
            with self.subTest(payload=payload), self.assertRaises(weather.WeatherError):
                weather.parse_forecast(payload)
        for field, value in (("startTime", "bad-date"), ("endTime", "2020-01-01 00:00:00"), ("parameter", [])):
            payload = fixture()
            payload["records"]["location"][0]["weatherElement"][0]["time"][0][field] = value
            with self.subTest(field=field), self.assertRaises(weather.WeatherError):
                weather.parse_forecast(payload)

    def test_bad_numbers_and_conflicting_values_rejected(self):
        for value in ("nan", "Infinity", "101", "-1", "rain"):
            payload = fixture()
            payload["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"] = value
            with self.subTest(value=value), self.assertRaises(weather.WeatherError):
                weather.parse_forecast(payload)
        payload = fixture()
        periods = payload["records"]["location"][0]["weatherElement"][0]["time"]
        conflicting = copy.deepcopy(periods[0])
        conflicting["parameter"]["parameterName"] = "other weather"
        periods.append(conflicting)
        with self.assertRaises(weather.WeatherError):
            weather.parse_forecast(payload)


class FetchTests(unittest.TestCase):
    def response(self, data):
        return io.BytesIO(data)

    @patch("weather.build_opener")
    def test_authorization_header_and_key_free_url(self, build):
        payload = fixture()
        build.return_value.open.return_value = self.response(json.dumps(payload).encode())
        self.assertEqual(weather.fetch_forecast("test-private-key"), payload)
        request = build.return_value.open.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "test-private-key")
        self.assertEqual(request.full_url, weather.CWA_URL)
        self.assertNotIn("test-private-key", request.full_url)
        self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 20)
        self.assertIsInstance(build.call_args.args[0], weather._NoRedirect)

    @patch("weather.build_opener")
    def test_invalid_json_and_api_failure_rejected(self, build):
        for data in (b"<html>private-key</html>", b'{"success":"false","message":"private-key"}', b"[]"):
            build.return_value.open.return_value = self.response(data)
            with self.subTest(data=data), self.assertRaises(weather.WeatherError) as caught:
                weather.fetch_forecast("private-key")
            self.assertNotIn("private-key", str(caught.exception))

    @patch("weather.build_opener")
    def test_network_and_http_errors_do_not_leak_keys(self, build):
        for error in (URLError("secret-key"), TimeoutError("secret-key"), HTTPError("https://example/secret-key", 401, "secret-key", {}, None), HTTPError("https://example", 429, "secret-key", {}, None), HTTPError("https://example", 500, "secret-key", {}, None)):
            build.return_value.open.side_effect = error
            with self.subTest(error=type(error).__name__), self.assertRaises(weather.WeatherError) as caught:
                weather.fetch_forecast("secret-key")
            self.assertNotIn("secret-key", str(caught.exception))

    @patch("weather.build_opener")
    def test_invalid_key_does_not_make_request(self, build):
        for key in (None, "", "  ", "secret\nHeader: x"):
            with self.subTest(key=key), self.assertRaises(weather.WeatherError):
                weather.fetch_forecast(key)
        build.assert_not_called()

    def test_redirects_never_forward_authorization(self):
        self.assertIsNone(weather._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com"))

    @patch("weather.build_opener")
    def test_response_size_bounded(self, build):
        with patch("weather.MAX_RESPONSE_BYTES", 8):
            build.return_value.open.return_value = self.response(b"a" * 20)
            with self.assertRaises(weather.WeatherError):
                weather.fetch_forecast("private-key")


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "weather.sqlite3"
        self.store = weather.WeatherStore(self.path)

    def test_roundtrip_and_source_isolation(self):
        self.assertIsNone(self.store.latest())
        actual = fixture()
        cwa_id = self.store.save(actual, fetched_at=NOW)
        demo_id = self.store.save(weather.demo_payload(NOW), source="demo", fetched_at=NOW)
        latest = weather.WeatherStore(self.path).latest()
        self.assertEqual(latest, {"id": cwa_id, "source": "cwa", "fetched_at": NOW.isoformat(), "rows": weather.parse_forecast(actual)})
        self.assertEqual(self.store.latest("demo")["id"], demo_id)
        self.assertEqual(self.store.history(1), [{"id": demo_id, "source": "demo", "fetched_at": NOW.isoformat(), "row_count": 66}])
        self.assertEqual(len(self.store.history()), 2)

    def test_demo_cannot_be_accidentally_marked_live(self):
        with self.assertRaises(weather.WeatherError):
            self.store.save(weather.demo_payload(NOW))
        self.assertEqual(self.store.history(), [])

    def test_invalid_snapshot_is_not_saved(self):
        self.store.save(fixture(), fetched_at=NOW)
        with self.assertRaises(weather.WeatherError):
            self.store.save({"success": "false"})
        with self.assertRaises(weather.WeatherError):
            self.store.save(fixture(), fetched_at=datetime(2026, 9, 24))
        self.assertEqual(len(self.store.history()), 1)

    def test_pruning_is_per_source_and_cascades_rows(self):
        cwa_id = self.store.save(fixture(), fetched_at=NOW)
        with patch("weather.MAX_SNAPSHOTS_PER_SOURCE", 2):
            for _ in range(3):
                self.store.save(weather.demo_payload(NOW), "demo", NOW)
        self.assertEqual(self.store.latest()["id"], cwa_id)
        self.assertEqual(len(self.store.history()), 3)
        with sqlite3.connect(self.path) as connection:
            count = connection.execute("SELECT count(*) FROM weather_rows").fetchone()[0]
            self.assertEqual(count, 3 + 2 * 66)

    def test_source_and_limit_validation(self):
        with self.assertRaises(weather.WeatherError):
            self.store.latest("unknown")
        with self.assertRaises(weather.WeatherError):
            self.store.save(fixture(), source="unknown")
        for limit in (0, -1, True, 1.5, "10"):
            with self.subTest(limit=limit), self.assertRaises(weather.WeatherError):
                self.store.history(limit)


if __name__ == "__main__":
    unittest.main()

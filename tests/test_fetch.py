import requests
from tracekpg import fetch


def test_network_failure_is_logged_and_does_not_crash(tmp_path, monkeypatch):
    log_file = tmp_path / "fetch_errors.log"
    monkeypatch.setattr(fetch, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch, "FETCH_LOG_FILE", str(log_file))

    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("network down")

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    fetch.fetch_article("Some_Company")

    assert "Some_Company" in log_file.read_text()
    assert not (tmp_path / "Some_Company.txt").exists()


class FakeResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def test_empty_extract_is_logged_and_not_saved(tmp_path, monkeypatch):
    log_file = tmp_path / "fetch_errors.log"
    monkeypatch.setattr(fetch, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch, "FETCH_LOG_FILE", str(log_file))
    monkeypatch.setattr(fetch, "REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResponse({"query": {"pages": {"-1": {"missing": ""}}}}))

    fetch.fetch_article("Missing_Page")

    assert "Missing_Page" in log_file.read_text()
    assert not (tmp_path / "Missing_Page.txt").exists()


def test_malformed_response_is_logged_and_does_not_crash(tmp_path, monkeypatch):
    log_file = tmp_path / "fetch_errors.log"
    monkeypatch.setattr(fetch, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch, "FETCH_LOG_FILE", str(log_file))
    monkeypatch.setattr(fetch, "REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResponse({"error": "bad"}))

    fetch.fetch_article("Broken_Page")

    assert "Broken_Page" in log_file.read_text()

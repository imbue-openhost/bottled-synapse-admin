from pathlib import Path

import pytest

from openhost_synapse_admin.session import InvalidSession
from openhost_synapse_admin.session import Session
from openhost_synapse_admin.session import load_session
from openhost_synapse_admin.session import parse_session
from openhost_synapse_admin.session import save_session

SESSION_VALUES = {
    "base_url": "https://matrix.example.com",
    "access_token": "syt_example",
    "user_id": "@admin:example.com",
    "device_id": "ABCDEFG",
    "home_server": "example.com",
}


def test_round_trips_through_disk(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    save_session(path, Session(values=SESSION_VALUES))
    assert load_session(path).values == SESSION_VALUES


def test_missing_file_reads_as_empty(tmp_path: Path) -> None:
    assert load_session(tmp_path / "session.json").values == {}


def test_saved_file_is_owner_only(tmp_path: Path) -> None:
    """The file holds a Matrix admin token, so it must not be group- or world-readable."""
    path = tmp_path / "session.json"
    save_session(path, Session(values=SESSION_VALUES))
    assert path.stat().st_mode & 0o077 == 0


def test_save_overwrites_previous_session(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    save_session(path, Session(values=SESSION_VALUES))
    save_session(path, Session(values={"base_url": "https://other.example.com"}))
    assert load_session(path).values == {"base_url": "https://other.example.com"}


def test_save_leaves_no_temp_files(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    save_session(path, Session(values=SESSION_VALUES))
    assert [p.name for p in tmp_path.iterdir()] == ["session.json"]


def test_parses_a_flat_string_map() -> None:
    assert parse_session(SESSION_VALUES).values == SESSION_VALUES


def test_parses_unknown_keys() -> None:
    """The frontend owns the schema; a key a future upstream release adds must survive."""
    assert parse_session({"some_new_key": "value"}).values == {"some_new_key": "value"}


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(["not", "an", "object"], id="list"),
        pytest.param("a string", id="string"),
        pytest.param({"key": 5}, id="non-string-value"),
        pytest.param({"key": None}, id="null-value"),
        pytest.param({"key": {"nested": "object"}}, id="nested-object"),
        pytest.param({"key": "x" * 9000}, id="value-too-long"),
        pytest.param({str(i): "v" for i in range(50)}, id="too-many-keys"),
    ],
)
def test_rejects_malformed_payloads(payload: object) -> None:
    with pytest.raises(InvalidSession):
        parse_session(payload)

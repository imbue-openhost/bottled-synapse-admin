import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import attr

# Mirrors what synapse-admin would otherwise keep in localStorage (base_url, access_token, user_id,
# device_id, home_server, and the transient sso_base_url). Deliberately not a fixed set of fields: the
# frontend owns the schema, and pinning it here would silently drop keys a future release adds.
MAX_VALUES = 32
MAX_VALUE_LENGTH = 8192


@attr.s(auto_attribs=True, frozen=True)
class Session:
    values: Mapping[str, str]

    @classmethod
    def empty(cls) -> "Session":
        return cls(values={})


class InvalidSession(Exception):
    """The frontend sent something that isn't a flat string->string map."""


def parse_session(payload: object) -> Session:
    if not isinstance(payload, dict):
        raise InvalidSession("session must be a JSON object")
    if len(payload) > MAX_VALUES:
        raise InvalidSession(f"session has more than {MAX_VALUES} keys")
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise InvalidSession("session keys and values must all be strings")
        if len(value) > MAX_VALUE_LENGTH:
            raise InvalidSession(f"value for {key!r} exceeds {MAX_VALUE_LENGTH} characters")
    return Session(values=dict(payload))


def load_session(path: Path) -> Session:
    if not path.exists():
        return Session.empty()
    return parse_session(json.loads(path.read_text()))


def save_session(path: Path, session: Session) -> None:
    """Write atomically and 0600 — this file holds a Matrix admin access token."""
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".session-")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(dict(session.values), handle, indent=2)
        tmp_path.chmod(0o600)
        tmp_path.replace(path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

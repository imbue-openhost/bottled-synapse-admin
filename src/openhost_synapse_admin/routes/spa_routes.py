import mimetypes
from pathlib import Path

from litestar import Response
from litestar import get
from litestar.response import File

from openhost_synapse_admin.config import Settings

_INDEX = "index.html"


def _resolve_static_file(static_dir: Path, request_path: str) -> Path | None:
    """Map a URL path to a file inside static_dir, or None if it isn't one. Rejects traversal outside the root."""
    relative = request_path.lstrip("/")
    if not relative:
        return None
    candidate = (static_dir / relative).resolve()
    if not candidate.is_relative_to(static_dir.resolve()):
        return None
    return candidate if candidate.is_file() else None


@get("/healthz", include_in_schema=False, sync_to_thread=False)
def healthz() -> Response[str]:
    return Response("ok", media_type="text/plain")


def _serve(static_dir: Path, request_path: str) -> File:
    """Serve a file from the build, falling back to index.html so client-side routes resolve."""
    static_file = _resolve_static_file(static_dir, request_path) or static_dir / _INDEX
    media_type, _ = mimetypes.guess_type(static_file.name)
    # Hashed build assets are immutable; index.html and config.json are not.
    cache_control = "public, max-age=31536000, immutable" if request_path.startswith("/assets/") else "no-cache"
    return File(
        path=static_file,
        media_type=media_type or "application/octet-stream",
        headers={"Cache-Control": cache_control},
        content_disposition_type="inline",
    )


# A ":path" param does not match an empty segment, so "/" needs its own handler.
@get("/", include_in_schema=False, sync_to_thread=False)
def serve_root(settings: Settings) -> File:
    return _serve(settings.static_dir, "/")


@get("/{request_path:path}", include_in_schema=False, sync_to_thread=False)
def serve_spa(request_path: str, settings: Settings) -> File:
    return _serve(settings.static_dir, request_path)

from litestar import Response
from litestar import get
from litestar import put
from litestar.exceptions import ClientException

from openhost_synapse_admin.config import Settings
from openhost_synapse_admin.session import InvalidSession
from openhost_synapse_admin.session import load_session
from openhost_synapse_admin.session import parse_session
from openhost_synapse_admin.session import save_session

SESSION_PATH = "/_openhost/session"

# The response body carries an admin access token; it must not be cached anywhere.
_NO_STORE = {"Cache-Control": "no-store"}


@get(SESSION_PATH, include_in_schema=False, sync_to_thread=False)
def read_session(settings: Settings) -> Response[dict[str, str]]:
    session = load_session(settings.session_path)
    return Response(dict(session.values), headers=_NO_STORE)


@put(SESSION_PATH, include_in_schema=False, sync_to_thread=False)
def write_session(data: object, settings: Settings) -> Response[None]:
    try:
        session = parse_session(data)
    except InvalidSession as error:
        raise ClientException(str(error)) from error
    save_session(settings.session_path, session)
    return Response(None, status_code=204, headers=_NO_STORE)

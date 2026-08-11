from litestar import Litestar
from litestar.di import Provide

from openhost_synapse_admin.config import Settings
from openhost_synapse_admin.config import load_settings
from openhost_synapse_admin.routes.session_routes import read_session
from openhost_synapse_admin.routes.session_routes import write_session
from openhost_synapse_admin.routes.spa_routes import healthz
from openhost_synapse_admin.routes.spa_routes import serve_root
from openhost_synapse_admin.routes.spa_routes import serve_spa


def create_app(settings: Settings | None = None) -> Litestar:
    resolved = settings if settings is not None else load_settings()
    return Litestar(
        # serve_spa is the catch-all and must stay last.
        route_handlers=[healthz, read_session, write_session, serve_root, serve_spa],
        dependencies={"settings": Provide(lambda: resolved, sync_to_thread=False, use_cache=True)},
    )

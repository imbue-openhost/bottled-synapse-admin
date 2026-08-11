import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from openhost_synapse_admin.app import create_app

PORT = 8080


def main() -> None:
    config = Config()
    config.bind = [f"0.0.0.0:{PORT}"]
    config.accesslog = "-"
    config.errorlog = "-"
    asyncio.run(serve(create_app(), config))  # type: ignore[arg-type]


if __name__ == "__main__":
    main()

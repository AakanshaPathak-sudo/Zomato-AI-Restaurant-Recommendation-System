"""Run API: python -m phase_6_web (from repository root)."""

from __future__ import annotations

import errno
import os
import sys

import uvicorn


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return int(raw)


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = _int_env("PORT", 8000)
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")

    open_url = f"http://127.0.0.1:{port}/" if host in ("0.0.0.0", "::", "[::]") else f"http://{host}:{port}/"
    print(
        f"\n  Open in your browser:  {open_url}\n"
        f"  Health:                http://127.0.0.1:{port}/health\n"
        f"  Run from repo root so imports and data/processed/restaurants.parquet resolve.\n"
        f"  If the port is busy:    PORT=8001 python3 -m phase_6_web\n"
        f"  Dev auto-reload:        UVICORN_RELOAD=1 python3 -m phase_6_web\n",
        file=sys.stderr,
    )

    try:
        uvicorn.run("phase_6_web.api:app", host=host, port=port, reload=reload)
    except OSError as e:
        in_use = e.errno == errno.EADDRINUSE or "address already in use" in str(e).lower()
        if in_use:
            print(
                f"Port {port} is already in use. Stop the other process or try:\n"
                f"  PORT={port + 1} python3 -m phase_6_web\n",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    main()

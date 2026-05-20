"""Export OpenAPI spec to openapi.json (run from /backend directory)."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    from src.main import app  # noqa: PLC0415

    spec = app.openapi()
    output_path = Path(__file__).parent.parent / "openapi.json"
    output_path.write_text(json.dumps(spec, indent=2))
    print(f"OpenAPI spec written to {output_path}")


if __name__ == "__main__":
    main()

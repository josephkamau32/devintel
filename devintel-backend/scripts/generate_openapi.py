"""Generate OpenAPI schema for DevIntel API.

Run this script to generate openapi.json for client SDK generation.
"""

import json
from pathlib import Path


def generate_openapi_schema() -> dict:
    """Generate and return the OpenAPI schema."""
    from app.main import app
    return app.openapi()


def main():
    schema = generate_openapi_schema()
    output_path = Path(__file__).parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"OpenAPI schema written to {output_path}")


if __name__ == "__main__":
    main()
#!/usr / bin / env python3
"""
Export OpenAPI specification to JSON file.

This script exports the FastAPI OpenAPI schema to a JSON file
that can be used for documentation, testing, or client generation.

Usage:
    python scripts / export_openapi.py

Output:
    - openapi.json: OpenAPI 3.0 specification
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.api.main import app


def export_openapi_spec(output_path: Path = None) -> None:
    """
    Export OpenAPI specification to JSON file.

    Args:
        output_path: Path to output file (default: openapi.json in project root)
    """
    if output_path is None:
        output_path = project_root / "openapi.json"

    # Get OpenAPI schema from FastAPI app
    openapi_schema = app.openapi()

    # Write to file with pretty formatting
    with open(output_path, "w", encoding="utf - 8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI specification exported to: {output_path}")
    print(f"📊 API Version: {openapi_schema.get('info', {}).get('version')}")
    print(f"📝 Total endpoints: {len(openapi_schema.get('paths', {}))}")
    print(f"🏷️  Total schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")


def main():
    """Main entry point."""
    try:
        export_openapi_spec()
        print("\n💡 Tip: Import openapi.json into Postman to generate API collection")
        print("💡 Tip: View interactive docs at http://localhost:8000 / docs")
    except Exception as e:
        print(f"❌ Error exporting OpenAPI spec: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

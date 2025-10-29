"""Fix async test decorators"""

import re

files = ["tests / test_cli_orchestrator.py", "tests / test_hybrid_engine.py"]

for file in files:
    with open(file, "r", encoding="utf - 8") as f:
        content = f.read()

    # Add pytest import if not present
    if "import pytest" not in content:
        content = content.replace("import asyncio", "import asyncio\nimport pytest")

    # Add @pytest.mark.asyncio decorator before async def test functions
    content = re.sub(r"\n(async def test_\w+\(\):)", r"\n@pytest.mark.asyncio\n\1", content)

    with open(file, "w", encoding="utf - 8") as f:
        f.write(content)

    print(f"Fixed {file}")

print("Done!")

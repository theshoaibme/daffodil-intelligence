"""
Daffodil Intelligence — Agent / Runtime smoke script.

Updated for the Antigravity runtime. Verifies:
  - the tool registry discovers all tools
  - tools are adapted for the Antigravity agent
  - the runtime reports availability
  - (optional) a live agent turn when GEMINI_API_KEY + RUN_LIVE_AGENT=1

Run:  python test_agents.py
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.registry import get_registry
from app.runtime.tool_adapter import get_antigravity_tools
from app.runtime.agent_factory import is_available
from app.runtime import session_manager, orchestrator


async def main():
    print("\n" + "=" * 60)
    print("DAFFODIL INTELLIGENCE — RUNTIME TEST SUITE")
    print("=" * 60)

    registry = get_registry()
    print(f"\nTool registry: {registry.count} tools across {len(registry.categories())} categories")
    for cat in sorted(registry.categories()):
        names = [t.name for t in registry.list_by_category(cat)]
        print(f"  - {cat}: {', '.join(names)}")

    tools = get_antigravity_tools()
    print(f"\nAdapted {len(tools)} tools for the Antigravity agent.")

    print(f"\nAntigravity runtime available: {is_available()}")

    # A couple of offline tool executions.
    print("\nSample tool calls:")
    cgpa = await registry.execute("get_cgpa", student_id="221-15-1234")
    print(f"  get_cgpa -> success={cgpa.success} data={cgpa.data}")
    books = await registry.execute("search_books", query="Clean")
    print(f"  search_books -> success={books.success}")

    if os.environ.get("RUN_LIVE_AGENT") == "1" and is_available():
        print("\nLive agent turn:")
        res = await orchestrator.run("Say hello in one short sentence.", user_id=1, chat_id="agents-script")
        print(f"  engine={res.get('engine')} content={res.get('content')[:200]!r}")
    else:
        print("\n(Set RUN_LIVE_AGENT=1 with a quota-enabled GEMINI_API_KEY for a live turn.)")

    print("\n" + "=" * 60)
    print("RUNTIME TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

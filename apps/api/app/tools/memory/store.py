"""Memory tools — let the agent store and recall long-term notes."""

from ..base import BaseTool, ToolParameter, ToolResult
from ...memory.semantic import semantic_memory


class StoreNoteTool(BaseTool):
    name = "store_note"
    description = "Save a note to long-term memory so it can be recalled later."
    category = "memory"
    parameters = [
        ToolParameter(name="text", type="string", description="The note/fact to remember"),
        ToolParameter(name="user_id", type="string", description="Owner id for the note", required=False, default="0"),
        ToolParameter(name="tag", type="string", description="Optional category/tag", required=False),
    ]

    async def execute(self, text: str, user_id: str = "0", tag: str = None) -> ToolResult:
        try:
            note = semantic_memory.add(text, user_id=user_id, metadata={"tag": tag} if tag else {})
            return self.ok({"id": note["id"], "stored": True})
        except Exception as e:
            return self.fail(str(e))


class RecallNotesTool(BaseTool):
    name = "recall_notes"
    description = "Search long-term memory for notes relevant to a query."
    category = "memory"
    parameters = [
        ToolParameter(name="query", type="string", description="What to search for in memory"),
        ToolParameter(name="user_id", type="string", description="Owner id to scope the search", required=False),
        ToolParameter(name="k", type="integer", description="Max notes to return (default 5)", required=False, default=5),
    ]

    async def execute(self, query: str, user_id: str = None, k: int = 5) -> ToolResult:
        try:
            notes = semantic_memory.search(query, user_id=user_id, k=k)
            return self.ok({
                "query": query,
                "notes": [{"text": n["text"], "metadata": n.get("metadata", {})} for n in notes],
                "count": len(notes),
            })
        except Exception as e:
            return self.fail(str(e))

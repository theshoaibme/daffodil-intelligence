"""Memory tools — let the agent store and recall long-term notes."""

from ..base import BaseTool, ToolParameter, ToolResult
from ...memory import memory_service


class StoreNoteTool(BaseTool):
    name = "store_note"
    description = "Save a note to long-term memory so it can be recalled later."
    category = "memory"
    parameters = [
        ToolParameter(name="text", type="string", description="The note/fact to remember"),
        ToolParameter(name="user_id", type="string", description="Owner id for the note", required=False, default="0"),
        ToolParameter(name="agent_id", type="string", description="Agent scope (default main)", required=False, default="main"),
        ToolParameter(name="memory_type", type="string", description="Memory type (fact, preference, episode)", required=False, default="fact"),
        ToolParameter(name="tag", type="string", description="Optional category/tag", required=False),
    ]

    async def execute(
        self,
        text: str,
        user_id: str = "0",
        agent_id: str = "main",
        memory_type: str = "fact",
        tag: str = None,
    ) -> ToolResult:
        try:
            metadata = {"tag": tag} if tag else {}
            note = await memory_service.remember(
                text,
                user_id=int(user_id or 0),
                agent_id=agent_id,
                memory_type=memory_type,
                visibility="shared" if agent_id == "main" else "private",
                source="agent",
                metadata=metadata,
            )
            return self.ok({"id": note.get("id"), "stored": True})
        except Exception as e:
            return self.fail(str(e))


class RecallNotesTool(BaseTool):
    name = "recall_notes"
    description = "Search long-term memory for notes relevant to a query."
    category = "memory"
    parameters = [
        ToolParameter(name="query", type="string", description="What to search for in memory"),
        ToolParameter(name="user_id", type="string", description="Owner id to scope the search", required=False),
        ToolParameter(name="agent_id", type="string", description="Agent scope", required=False, default="main"),
        ToolParameter(name="memory_type", type="string", description="Filter by memory type", required=False),
        ToolParameter(name="k", type="integer", description="Max notes to return (default 5)", required=False, default=5),
    ]

    async def execute(
        self,
        query: str,
        user_id: str = None,
        agent_id: str = "main",
        memory_type: str = None,
        k: int = 5,
    ) -> ToolResult:
        try:
            types = [memory_type] if memory_type else None
            notes = await memory_service.recall(
                query,
                user_id=int(user_id or 0),
                agent_id=agent_id,
                memory_types=types,
                k=k,
            )
            return self.ok({
                "query": query,
                "notes": [
                    {
                        "text": n.get("content", n.get("text", "")),
                        "memory_type": n.get("memory_type"),
                        "metadata": n.get("metadata", {}),
                    }
                    for n in notes
                ],
                "count": len(notes),
            })
        except Exception as e:
            return self.fail(str(e))


class ListMemoriesTool(BaseTool):
    name = "list_memories"
    description = "List stored memories for the current user, optionally filtered by type or agent."
    category = "memory"
    parameters = [
        ToolParameter(name="user_id", type="string", description="Owner id", required=False, default="0"),
        ToolParameter(name="agent_id", type="string", description="Filter by agent", required=False),
        ToolParameter(name="memory_type", type="string", description="Filter by memory type", required=False),
        ToolParameter(name="limit", type="integer", description="Max items", required=False, default=20),
    ]

    async def execute(
        self,
        user_id: str = "0",
        agent_id: str = None,
        memory_type: str = None,
        limit: int = 20,
    ) -> ToolResult:
        try:
            result = await memory_service.list_memories(
                int(user_id or 0),
                agent_id=agent_id,
                memory_type=memory_type,
                limit=limit,
            )
            return self.ok(result)
        except Exception as e:
            return self.fail(str(e))

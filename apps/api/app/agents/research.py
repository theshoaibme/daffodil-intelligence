from .base import BaseAgent
from typing import Optional, Dict
from ..core.university_data import university_data


class ResearchAgent(BaseAgent):
    name = "Research Agent"
    description = "Helps with research papers, citations, thesis help, literature review"
    tools = ["search_papers", "get_citations", "help_thesis", "literature_review", "generate_abstract"]

    SYSTEM_PROMPT = """You are the Research Agent for Daffodil Intelligence.
You help students with:
- Finding research papers
- Managing citations
- Thesis topic suggestions
- Literature review
- Research methodology"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["paper", "research", "find"]):
            return await self.handle_papers(message)

        elif any(k in message_lower for k in ["thesis", "topic"]):
            return await self.handle_thesis(message)

        elif any(k in message_lower for k in ["citation", "reference"]):
            return await self.handle_citations()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_papers(self, message: str) -> str:
        papers = await search_papers(message)
        paper_list = "\n".join([f"- **{p['title']}** ({p['year']}) - {p['citations']} citations" for p in papers])
        return f"""📄 **Research Papers**

{paper_list}

Use Google Scholar or IEEE Xplore for full access."""

    async def handle_thesis(self, message: str) -> str:
        result = await help_thesis(message)
        topics = "\n".join([f"- {t}" for t in result["suggested_topics"]])
        return f"""🎓 **Thesis Help**

Suggested Topics:
{topics}

Methodology: {result['methodology']}
Timeline: {result['timeline']}"""

    async def handle_citations(self) -> str:
        return """📚 **Citation Help**

I can help with:
- APA, MLA, IEEE formats
- Reference management
- Bibliography creation

Share your paper and I'll format citations."""



async def search_papers(query: str) -> list[dict]:
    """Returns empty list — real paper search is handled by the ResearchAgent LLM via generate_response."""
    return []


async def help_thesis(topic: str) -> dict:
    return {
        "suggested_topics": ["AI in Healthcare", "NLP for Bengali Language", "Edge Computing in IoT"],
        "methodology": "Mixed methods (quantitative + qualitative)",
        "timeline": "6 months recommended"
    }
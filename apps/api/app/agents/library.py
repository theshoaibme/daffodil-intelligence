from .base import BaseAgent
from typing import Optional, Dict
import logging
from ..core.university_data import university_data

logger = logging.getLogger(__name__)


class LibraryAgent(BaseAgent):
    name = "Library Agent"
    description = "Handles books, journals, PDFs, research papers, and library services"
    tools = ["search_books", "check_availability", "reserve_book", "get_journals", "download_pdf"]

    SYSTEM_PROMPT = """You are the Library Agent for Daffodil Intelligence.
You help students with:
- Searching for books and journals
- Checking book availability
- Reserving books
- Finding research papers
- PDF downloads

Use library tools when available. Be accurate about availability."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["search", "find", "look for"]):
            return await self.handle_search(message)

        elif any(k in message_lower for k in ["available", "borrow", "check"]):
            return await self.handle_availability(message)

        elif any(k in message_lower for k in ["reserve", "book"]):
            return await self.handle_reserve(message)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_search(self, message: str) -> str:
        import re
        query = re.search(r'(?:search|find|look for)\s+(?:books?\s+)?(.+)', message.lower())
        search_term = query.group(1) if query else message
        books = await search_books(search_term)

        if not books:
            return f"📚 No books found matching '{search_term}'. Try a different search term."

        book_list = "\n".join([
            f"- **{b['title']}** by {b['author']} (Available: {b['available']})"
            for b in books
        ])

        return f"""📚 **Search Results**

{book_list}

Location: CS Section
Use the 'check_availability' tool to confirm before visiting."""

    async def handle_availability(self, message: str) -> str:
        import re
        match = re.search(r'[\w\s]+', message.replace("available", "").replace("check", ""))
        book_title = match.group() if match else message

        result = await check_availability(book_title)
        return f"""📖 **Availability Check**

Book: {book_title}
Available: **{result['available']} copies**
Location: {result['location']}"""

    async def handle_reserve(self, message: str) -> str:
        return """📌 **Reserve Book**

To reserve a book:
1. Search for the book first
2. Note the book title
3. Visit the library counter with your student ID

Or I can help you check availability first."""


async def search_books(query: str, limit: int = 10) -> list[dict]:
    books = await university_data.search_books(query, limit)
    return [{"title": b["title"], "author": b["author"], "available": b["available"], "location": "Library CS Section"} for b in books]


async def check_availability(book_title: str) -> dict:
    books = await university_data.search_books(book_title, 1)
    if books:
        b = books[0]
        avail = await university_data.get_book_availability(b["id"])
        return {"available": avail.get("available", 0), "location": "Library"}
    return {"available": 0, "location": "Not found"}
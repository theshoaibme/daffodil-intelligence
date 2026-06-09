"""
Antigravity Agent Runtime
=========================
Wraps the Google Antigravity SDK as the single agent runtime for Daffodil
Intelligence. Exposes the main agent, tool adapters, session management and
policy configuration used by the API, Telegram bot and voice subsystems.
"""

from .session_manager import session_manager, SessionManager
from .agent_factory import build_agent, AgentPersona

__all__ = ["session_manager", "SessionManager", "build_agent", "AgentPersona"]

"""Generate scholarly auto-replies for connected research network nodes."""

from __future__ import annotations

import random
import re

from .build_network import NetworkNode

_PURPOSE_ACKS = {
    "collaboration": [
        "Thank you for your collaboration inquiry. I am encouraged by the overlap between our work in {focus} and would welcome a deeper discussion.",
        "I appreciate your interest in collaborating. Your message regarding {focus} resonates with our current research priorities.",
    ],
    "research-discussion": [
        "Thank you for your thoughtful message. I would be happy to exchange ideas on {focus} and related literature.",
        "I received your research discussion note and agree there is meaningful ground to explore around {focus}.",
    ],
    "institutional-inquiry": [
        "Thank you for reaching out regarding institutional engagement. We are open to exploring partnership opportunities in {focus}.",
        "Your institutional inquiry has been received. Our research office will review opportunities aligned with {focus}.",
    ],
}

_GENERAL_ACKS = [
    "Thank you for your message. I would be glad to continue this correspondence about {focus}.",
    "I appreciate you reaching out. Let us continue the conversation around our shared interests in {focus}.",
    "Your note is well received. I look forward to further exchange on {focus} and related publications.",
]

_FOLLOW_UPS = [
    "Would you be available for a brief virtual meeting next week to discuss next steps?",
    "Please feel free to share any preprints or project outlines that would help us identify concrete collaboration paths.",
    "If helpful, I can also connect you with colleagues in our group who focus on adjacent topics.",
]


def _first_name(node: NetworkNode) -> str:
    if node.kind == "institution":
        return node.name
    parts = re.findall(r"[A-Z][a-z]+", node.name)
    return parts[-1] if parts else node.name


def build_auto_reply(node: NetworkNode, *, purpose: str | None, user_body: str) -> tuple[str, str]:
    """Return (subject, body) for an incoming reply from the connection target."""
    focus = node.focus or "interdisciplinary research"
    pool = _PURPOSE_ACKS.get(purpose or "", _GENERAL_ACKS)
    opener = random.choice(pool).format(focus=focus)
    follow_up = random.choice(_FOLLOW_UPS)

    snippet = user_body.strip().split("\n")[0][:120]
    if len(user_body.strip()) > 120:
        snippet += "…"

    body = (
        f"Dear Colleague,\n\n"
        f"{opener}\n\n"
        f'Regarding your note — "{snippet}" — I believe there is a productive path forward.\n\n'
        f"{follow_up}\n\n"
        f"Warm regards,\n{_first_name(node)}\n{node.subtitle}"
    )
    subject = f"Re: Collaboration — {node.focus.split(' · ')[0]}"
    return subject, body

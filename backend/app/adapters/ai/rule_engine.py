"""Deterministic fallback "AI".

Answers supported questions with direct database queries. This is the
default adapter: the assistant and builder keep working when no
external AI provider is configured or enabled.
"""

from app.adapters.ai.base import AIAdapter


class RuleEngineAdapter(AIAdapter):
    name = "rule_engine"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # The assistant service composes answers itself using this adapter
        # as a marker that deterministic handling is in effect.
        return ""

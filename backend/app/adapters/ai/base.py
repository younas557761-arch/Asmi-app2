from abc import ABC, abstractmethod


class AIAdapter(ABC):
    """Provider-independent AI interface.

    Implementations must never see raw school records beyond what the
    caller passes, and must handle their own timeouts/retries. Core
    school operations do not depend on any adapter being configured.
    """

    name = "base"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a text completion for the given prompts."""
        raise NotImplementedError


class AIUnavailableError(Exception):
    """Raised when no AI provider is configured and a task truly needs one."""

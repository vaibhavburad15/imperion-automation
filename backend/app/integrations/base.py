"""Base integration interface."""
from typing import Dict, Any


class BaseIntegration:
    """All integrations implement `execute(action, config, payload)`.

    `action` is the operation requested by the workflow node (e.g. 'send').
    `config` merges the workspace-level integration config with the node config.
    `payload` is the run context / data passed through the workflow.

    Returns a dict that becomes the node's output and is merged into context.
    """
    provider: str = "base"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

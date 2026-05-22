"""Workflow execution engine.

A workflow is a graph of nodes. Each node has:
  - id: str
  - type: 'trigger' | 'condition' | 'action' | 'follow_up' | 'delay'
  - config: dict
  - next: id of next node (or branches: {true: id, false: id} for conditions)

The engine walks the graph starting from the trigger node, evaluating each
node, accumulating output into a shared context, and recording step logs.

Retries with exponential backoff are applied at the *node* level.
Failures are isolated — an "on_failure" branch (if defined) is taken,
otherwise the run is marked failed.
"""
import time
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.logger import logger
from app.core.config import settings
from app.integrations import get_integration


class WorkflowEngine:

    def __init__(self, workflow, run, db):
        self.workflow = workflow
        self.run = run
        self.db = db
        self.context: Dict[str, Any] = dict(run.trigger_payload or {})
        self.context["_workspace_id"] = workflow.workspace_id
        self.step_logs = []

    # ---------- public ----------
    def execute(self) -> Dict[str, Any]:
        start_ts = time.time()
        self.run.status = "running"
        self.run.started_at = datetime.utcnow()
        self.db.commit()

        try:
            nodes = {n["id"]: n for n in self.workflow.graph.get("nodes", [])}
            if not nodes:
                raise ValueError("Workflow has no nodes")

            # Find trigger node (entry point)
            trigger_node = next(
                (n for n in nodes.values() if n.get("type") == "trigger"), None
            )
            if not trigger_node:
                # fallback: first node
                trigger_node = list(nodes.values())[0]

            current_id: Optional[str] = trigger_node["id"]
            visited = set()

            while current_id:
                if current_id in visited:
                    raise RuntimeError(f"Loop detected at node {current_id}")
                visited.add(current_id)

                node = nodes.get(current_id)
                if not node:
                    break

                next_id = self._execute_node(node)
                current_id = next_id

            self.run.status = "success"
            self.run.finished_at = datetime.utcnow()
            self.run.duration_ms = int((time.time() - start_ts) * 1000)
            self.run.context = self.context
            self.run.step_logs = self.step_logs
            self.db.commit()
            return {"status": "success", "context": self.context}

        except Exception as e:
            logger.exception(f"Workflow run {self.run.id} failed")
            self.run.status = "failed"
            self.run.error = str(e)[:1000]
            self.run.finished_at = datetime.utcnow()
            self.run.duration_ms = int((time.time() - start_ts) * 1000)
            self.run.step_logs = self.step_logs
            self.db.commit()
            return {"status": "failed", "error": str(e)}

    # ---------- per-node ----------
    def _execute_node(self, node: Dict[str, Any]) -> Optional[str]:
        node_id = node["id"]
        node_type = node.get("type", "action")
        node_label = node.get("label", node_id)
        log_entry = {
            "node_id": node_id,
            "label": node_label,
            "type": node_type,
            "status": "running",
            "ts": datetime.utcnow().isoformat(),
        }

        try:
            if node_type == "trigger":
                # Trigger node is implicitly already fired
                log_entry.update({"status": "success", "output": "trigger fired"})
                next_id = node.get("next")

            elif node_type == "condition":
                result = self._evaluate_condition(node.get("config", {}))
                log_entry.update({"status": "success", "output": {"matched": result}})
                branches = node.get("branches") or {}
                next_id = branches.get("true" if result else "false") or node.get("next")

            elif node_type == "delay":
                seconds = int(node.get("config", {}).get("seconds", 0))
                time.sleep(min(seconds, 30))  # cap in sync executor
                log_entry.update({"status": "success", "output": f"delayed {seconds}s"})
                next_id = node.get("next")

            elif node_type in ("action", "follow_up"):
                output = self._execute_action_with_retry(node)
                # merge output into context
                if isinstance(output, dict):
                    self.context.update({f"{node_id}.{k}": v for k, v in output.items()})
                    self.context.update(output)
                log_entry.update({"status": "success", "output": output})
                next_id = node.get("next")

            else:
                raise ValueError(f"Unknown node type: {node_type}")

        except Exception as e:
            log_entry.update({"status": "failed", "error": str(e)[:500]})
            self.step_logs.append(log_entry)
            on_fail = node.get("on_failure")
            if on_fail:
                return on_fail
            raise

        self.step_logs.append(log_entry)
        return next_id

    # ---------- helpers ----------
    def _execute_action_with_retry(self, node: Dict[str, Any]) -> Dict[str, Any]:
        cfg = node.get("config", {})
        provider = cfg.get("provider")
        action = cfg.get("action", "send")
        max_retries = int(cfg.get("max_retries", settings.MAX_RETRIES))

        last_err = None
        for attempt in range(max_retries + 1):
            try:
                integ = get_integration(provider)
                # Substitute templating in config values
                rendered_cfg = self._render_config(cfg, self.context)
                return integ.execute(action, rendered_cfg, self.context)
            except Exception as e:
                last_err = e
                self.run.retry_count += 1
                self.db.commit()
                if attempt < max_retries:
                    backoff = settings.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"Node {node['id']} attempt {attempt+1} failed: {e}; retry in {backoff}s")
                    time.sleep(backoff)
                else:
                    raise
        raise last_err

    def _evaluate_condition(self, cfg: Dict[str, Any]) -> bool:
        """Simple condition: {field, op, value} where op in eq/neq/gt/lt/contains/exists."""
        field = cfg.get("field", "")
        op = cfg.get("op", "eq")
        target = cfg.get("value")
        actual = self.context.get(field)

        if op == "eq":     return actual == target
        if op == "neq":    return actual != target
        if op == "gt":     return (actual or 0) > (target or 0)
        if op == "lt":     return (actual or 0) < (target or 0)
        if op == "contains": return target in (actual or "")
        if op == "exists": return actual is not None
        return False

    @staticmethod
    def _render_config(cfg: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Replace {{var}} placeholders in string config values."""
        def render(v):
            if isinstance(v, str):
                out = v
                for k, val in ctx.items():
                    out = out.replace(f"{{{{{k}}}}}", str(val))
                return out
            if isinstance(v, dict):
                return {kk: render(vv) for kk, vv in v.items()}
            if isinstance(v, list):
                return [render(x) for x in v]
            return v
        return {k: render(v) for k, v in cfg.items()}
